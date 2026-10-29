"""Throttle cơ sở của API (05 mục 5).

Khoá theo IP dùng `pii_hmac(request.client_ip)`, không bao giờ là IP thô; `client_ip` do
`shared.api.client_ip.ClientIpMiddleware` gán. Scope riêng thêm ở mốc dùng tới.
"""

from typing import TYPE_CHECKING, Any

from rest_framework.request import Request
from rest_framework.throttling import SimpleRateThrottle

from shared.privacy import pii_hmac

if TYPE_CHECKING:
    # rest_framework.views đọc DEFAULT_THROTTLE_CLASSES lúc import: import thật gây vòng
    from rest_framework.views import APIView


def _is_authenticated(request: Request) -> bool:
    return bool(request.user and request.user.is_authenticated)


class ClientIpRateThrottle(SimpleRateThrottle):
    """Đếm theo IP đã xác minh, khoá là HMAC của IP."""

    def get_cache_key(self, request: Request, view: APIView) -> str | None:
        client_ip: str = request.client_ip  # type: ignore[attr-defined]
        return self.cache_format % {"scope": self.scope, "ident": pii_hmac(client_ip)}


class AnonThrottle(ClientIpRateThrottle):
    """Request ẩn danh: 120/phút/IP."""

    scope = "anon"

    def get_cache_key(self, request: Request, view: APIView) -> str | None:
        if _is_authenticated(request):
            return None
        return super().get_cache_key(request, view)


class AccountThrottle(SimpleRateThrottle):
    """Request đã đăng nhập: 300/phút/Tài khoản; ẩn danh không bị lớp này đếm."""

    scope = "account"

    def get_cache_key(self, request: Request, view: APIView) -> str | None:
        if not _is_authenticated(request):
            return None
        user: Any = request.user
        return self.cache_format % {"scope": self.scope, "ident": user.pk}
