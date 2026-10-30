"""Tạo và quản lý Tài khoản (02 mục 6.1, 7.1)."""

from django.db import IntegrityError, transaction

from modules.identity.constants import AccountKind
from modules.identity.exceptions import EmailAlreadyUsed
from modules.identity.models import Account

STAFF_KINDS = frozenset({AccountKind.STAFF, AccountKind.ADMIN})


def create_staff_account(
    *, email: str, password: str, kind: AccountKind, full_name: str = ""
) -> Account:
    """Tạo Tài khoản Staff hoặc Admin cho back-office (US-1001 AC2, AC3).

    Email được chuẩn hoá về chữ thường; mỗi email thuộc tối đa một Tài khoản với mọi `kind`
    (05 mục 2.3). Độ mạnh mật khẩu do bên gọi kiểm trước bằng `validate_password`.

    Raises:
        EmailAlreadyUsed: Email đã thuộc một Tài khoản khác, không phân biệt hoa thường.
        ValueError: `kind` không phải `staff` hoặc `admin` (lỗi của bên gọi).
    """
    if kind not in STAFF_KINDS:
        raise ValueError(f"create_staff_account không tạo Tài khoản kind={kind}")
    account = Account(email=Account.objects.normalize_email(email), kind=kind, full_name=full_name)
    account.set_password(password)
    try:
        with transaction.atomic():
            if Account.objects.filter(email__iexact=account.email).exists():
                raise EmailAlreadyUsed()
            account.save()
    except IntegrityError as exc:
        # Hai lệnh tạo cùng email chạy song song: cả hai qua bước kiểm, UNIQUE(lower(email)) chặn
        raise EmailAlreadyUsed() from exc
    return account
