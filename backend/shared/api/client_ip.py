"""Gán `request.client_ip`: IP mà throttle tính hạn mức (ADR 0009, 05 mục 5).

Mọi request đi qua Next.js nên `REMOTE_ADDR` là IP của BFF. Chỉ tin `X-Client-IP` khi
`X-BFF-Secret` khớp một secret trong `BFF_SHARED_SECRETS` và giá trị là IPv4/IPv6 hợp lệ;
ngược lại dùng `REMOTE_ADDR`.
"""

import hmac
import ipaddress
from collections.abc import Callable

import structlog
from django.conf import settings
from django.http import HttpRequest, HttpResponse

logger = structlog.get_logger(__name__)


def _secret_matches(provided: str) -> bool:
    # So với mọi secret, không dừng sớm, để thời gian không lộ secret nào khớp
    matched = False
    for secret in settings.BFF_SHARED_SECRETS:
        matched |= hmac.compare_digest(provided.encode(), secret.encode())
    return matched


def resolve_client_ip(request: HttpRequest) -> str:
    remote_addr: str = request.META.get("REMOTE_ADDR", "")
    provided = request.headers.get("X-BFF-Secret")
    if provided is None or not _secret_matches(provided):
        return remote_addr
    claimed = request.headers.get("X-Client-IP")
    if claimed is None:
        return remote_addr
    try:
        return str(ipaddress.ip_address(claimed.strip()))
    except ValueError:
        # Không ghi giá trị header: có thể là IP thô hoặc dữ liệu tuỳ ý
        logger.warning("client_ip_invalid")
        return remote_addr


class ClientIpMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        request.client_ip = resolve_client_ip(request)  # type: ignore[attr-defined]
        return self.get_response(request)
