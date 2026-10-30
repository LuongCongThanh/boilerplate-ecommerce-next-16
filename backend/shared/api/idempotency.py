"""Xử lý header `Idempotency-Key` (04 mục 1, 03 mục 1.5).

Hàm hai bước, không bọc view: view kiểm quyền/sở hữu rồi gọi `begin(request)`. Nhận `Claim`
thì chạy tác động nghiệp vụ và gọi `claim.complete(...)` bên trong `transaction.atomic` của
mình, để kết quả idempotency commit cùng tác động. Nhận `Replay` hoặc `Pending` thì trả
`outcome.response()`.
"""

import hashlib
import json
import uuid
from dataclasses import dataclass
from datetime import timedelta
from types import TracebackType
from typing import Any, Self, cast

from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response

from shared.exceptions import DomainError
from shared.models import IdempotencyKey, IdempotencyStatus, uuid7

KEY_HEADER = "Idempotency-Key"
CART_HEADER = "X-Cart-Token"
# Thời gian một worker giữ key đang xử lý trước khi worker khác được giành lại
LEASE = timedelta(seconds=60)
RETRY_AFTER_SECONDS = 3


class IdempotencyConflict(DomainError):
    code = "IDEMPOTENCY_CONFLICT"
    http_status = 409
    message = _("Idempotency-Key đã được dùng cho một yêu cầu có nội dung khác.")


class LeaseLost(Exception):
    """Lease của `Claim` đã bị worker khác giành lại; tác động nghiệp vụ phải rollback."""


@dataclass(frozen=True)
class Replay:
    """Key đã `completed`: trả nguyên status và body đã lưu."""

    status: int
    body: Any

    def response(self) -> Response:
        return Response(self.body, status=self.status)


@dataclass(frozen=True)
class Pending:
    """Lần gửi trước với cùng key còn đang xử lý."""

    retry_after: int = RETRY_AFTER_SECONDS

    def response(self) -> Response:
        """`202 IdempotencyPendingDTO` (04 mục 5.2); endpoint cần body 202 khác tự dựng."""
        return Response(
            {"code": "IDEMPOTENCY_IN_PROGRESS", "retry_after": self.retry_after},
            status=202,
            headers={"Retry-After": str(self.retry_after)},
        )


@dataclass(frozen=True)
class Claim:
    """Request này giữ key; tác động nghiệp vụ chạy đúng một lần dưới `operation_id`.

    Dùng làm context manager bọc ngoài `transaction.atomic` của tác động: exception thoát ra
    thì nhả key để gửi lại cùng key chạy lại từ đầu.
    """

    key_id: uuid.UUID
    operation_id: uuid.UUID
    lease_token: uuid.UUID

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if exc_type is None:
            return
        # Chỉ xoá khi lease còn của mình; có `resource_id` thì giữ dòng cho luồng khôi phục
        with transaction.atomic():
            IdempotencyKey.objects.filter(
                pk=self.key_id, lease_token=self.lease_token, resource_id__isnull=True
            ).delete()

    def complete(self, status: int, body: Any, resource_id: uuid.UUID | None = None) -> None:
        """Lưu kết quả để replay; gọi bên trong `transaction.atomic` của tác động nghiệp vụ.

        Raises:
            LeaseLost: Lease đã hết và worker khác đã giành lại key.
        """
        row = IdempotencyKey.objects.select_for_update().get(pk=self.key_id)
        if row.lease_token != self.lease_token:
            raise LeaseLost
        row.status = IdempotencyStatus.COMPLETED
        row.completed_at = timezone.now()
        row.response_status = status
        row.response_body = body
        row.resource_id = resource_id
        row.lease_token = None
        row.lease_expires_at = None
        row.save()


def begin(request: Request) -> Claim | Replay | Pending:
    """Claim key bằng transaction ngắn, hoặc trả kết quả của lần gửi trước.

    Raises:
        ValidationError: Thiếu `Idempotency-Key`, key không phải UUID, hoặc request không có
            danh tính (Tài khoản hay `X-Cart-Token`).
        IdempotencyConflict: Cùng key nhưng body khác lần gửi trước.
    """
    key = _parse_key(request)
    scope = _scope(request)
    request_hash = _request_hash(request.data)
    lease_token = uuid7()
    now = timezone.now()

    # Transaction ngắn: trả về hoặc raise ở đây đều nhả khoá dòng ngay
    with transaction.atomic():
        row, created = IdempotencyKey.objects.select_for_update().get_or_create(
            scope=scope,
            key=key,
            defaults={
                "request_hash": request_hash,
                "lease_token": lease_token,
                "lease_expires_at": now + LEASE,
            },
        )
        if created:
            return Claim(key_id=row.pk, operation_id=row.operation_id, lease_token=lease_token)
        if row.request_hash != request_hash:
            raise IdempotencyConflict
        if row.status == IdempotencyStatus.COMPLETED:
            # CHECK `completed_has_response` bảo đảm `response_status` có giá trị
            return Replay(status=cast(int, row.response_status), body=row.response_body)
        if row.lease_expires_at and row.lease_expires_at > now:
            return Pending()
        # Lease đã hết: giành lại key, giữ `operation_id`; worker cũ sẽ hỏng ở `complete`
        row.lease_token = lease_token
        row.lease_expires_at = now + LEASE
        row.save(update_fields=["lease_token", "lease_expires_at", "updated_at"])
        return Claim(key_id=row.pk, operation_id=row.operation_id, lease_token=lease_token)


def _parse_key(request: Request) -> uuid.UUID:
    try:
        return uuid.UUID(request.headers.get(KEY_HEADER, ""))
    except ValueError:
        raise ValidationError({KEY_HEADER: [_("Cần header Idempotency-Key dạng UUID.")]}) from None


def _scope(request: Request) -> str:
    """`"{METHOD} {path}|{identity}"`; path đã gồm ID/mã tài nguyên, bỏ `/` cuối."""
    user: Any = request.user
    if user and user.is_authenticated:
        identity = f"account:{user.pk}"
    elif token := request.headers.get(CART_HEADER):
        # Không lưu token thô của giỏ
        identity = f"cart:{hashlib.sha256(token.encode()).hexdigest()}"
    else:
        message = _("Cần đăng nhập hoặc gửi X-Cart-Token để dùng Idempotency-Key.")
        raise ValidationError({CART_HEADER: [message]})
    return f"{request.method} {request.path.rstrip('/')}|{identity}"


def _request_hash(data: Any) -> str:
    """SHA-256 của body đã parse, chuẩn hoá để thứ tự key không đổi hash."""
    canonical = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode()).hexdigest()
