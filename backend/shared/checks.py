"""System check chạy bằng `manage.py check --deploy` trước khi triển khai."""

from typing import Any

from django.conf import settings
from django.core.checks import CheckMessage, Error, Tags, register

PII_HMAC_MIN_SECRET_BYTES = 32


@register(Tags.security, deploy=True)
def check_pii_hmac_key_length(**kwargs: Any) -> list[CheckMessage]:
    # Không gian số điện thoại Việt Nam nhỏ, khoá yếu thì vét cạn được (ADR 0016). Chỉ chặn
    # khi deploy để local và CI dùng được khoá ngắn
    weak = [
        kid
        for kid, secret in settings.PII_HMAC_KEYS
        if len(secret.encode()) < PII_HMAC_MIN_SECRET_BYTES
    ]
    if not weak:
        return []
    return [
        Error(
            f"Secret của kid {', '.join(weak)} trong PII_HMAC_KEYS ngắn hơn "
            f"{PII_HMAC_MIN_SECRET_BYTES} byte",
            id="shared.E001",
        )
    ]
