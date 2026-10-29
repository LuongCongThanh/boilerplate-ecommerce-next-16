"""HMAC cho định danh cá nhân bằng keyring `PII_HMAC_KEYS` (ADR 0016).

Dùng cho bằng chứng sau ẩn danh, IP trong log và key failure ledger. Hàm không tự chuẩn hoá
đầu vào: bên gọi đưa số E.164 (`shared.phones.normalize_vn_phone`) hoặc IP đã chuẩn.
"""

import hashlib
import hmac

from django.conf import settings


def _digest(kid: str, secret: str, value: str) -> str:
    mac = hmac.new(secret.encode(), value.encode(), hashlib.sha256).hexdigest()
    return f"{kid}:{mac}"


def pii_hmac(value: str) -> str:
    """Trả `<kid>:<hex>` bằng khoá đầu của keyring, dùng khi ghi giá trị mới."""
    kid, secret = settings.PII_HMAC_KEYS[0]
    return _digest(kid, secret, value)


def pii_hmac_candidates(value: str) -> list[str]:
    """Trả giá trị HMAC với mọi khoá còn trong keyring, để tra cứu bằng `__in`.

    Giá trị cũ có thể được ghi bằng khoá đã xoay; khoá cũ không bị xoá khỏi keyring.
    """
    return [_digest(kid, secret, value) for kid, secret in settings.PII_HMAC_KEYS]
