"""Lỗi nghiệp vụ của identity (02 mục 6.1)."""

from django.utils.translation import gettext_lazy as _

from shared.exceptions import DomainError


class EmailAlreadyUsed(DomainError):
    """Email đã thuộc một Tài khoản khác, không phân biệt hoa thường và `kind` (05 mục 2.3)."""

    code = "EMAIL_ALREADY_USED"
    http_status = 409
    message = _("Email đã được dùng cho một Tài khoản khác.")
