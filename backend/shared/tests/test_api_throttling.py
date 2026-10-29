from types import SimpleNamespace
from typing import Any

import pytest
import redis.exceptions
from django.test import override_settings
from rest_framework.request import Request
from rest_framework.test import APIClient, APIRequestFactory, force_authenticate
from rest_framework.throttling import SimpleRateThrottle
from rest_framework.views import APIView
from structlog.testing import capture_logs

from shared.api.throttling import AccountThrottle, AnonThrottle
from shared.privacy import pii_hmac


def drf_request(user: Any = None) -> Request:
    django_request = APIRequestFactory().get("/")
    if user is not None:
        force_authenticate(django_request, user=user)
    django_request.client_ip = "203.0.113.7"  # type: ignore[attr-defined]
    return APIView().initialize_request(django_request)


def test_account_throttle_keys_authenticated_user_by_pk() -> None:
    request = drf_request(SimpleNamespace(pk=42, is_authenticated=True))

    assert AccountThrottle().get_cache_key(request, APIView()) == "throttle_account_42"
    assert AnonThrottle().get_cache_key(request, APIView()) is None


def test_account_throttle_ignores_anonymous() -> None:
    assert AccountThrottle().get_cache_key(drf_request(), APIView()) is None


class DownCache:
    """Cache giả như RedisCache khi Redis tắt: mọi thao tác ném lỗi kết nối."""

    def get(self, *args: Any, **kwargs: Any) -> Any:
        raise redis.exceptions.ConnectionError("Error 111 connecting to redis:6379")

    set = get


@pytest.fixture
def cache_down(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(SimpleRateThrottle, "cache", DownCache())


@pytest.mark.urls("shared.tests.api_urls")
@pytest.mark.usefixtures("cache_down")
def test_cache_down_allows_request_and_logs_without_ip() -> None:
    with override_settings(BFF_SHARED_SECRETS=("secret-new",)), capture_logs() as logs:
        response = APIClient().get(
            "/items",
            REMOTE_ADDR="10.0.0.5",
            HTTP_X_BFF_SECRET="secret-new",
            HTTP_X_CLIENT_IP="203.0.113.7",
        )

    assert response.status_code == 200
    warnings = [log for log in logs if log["event"] == "throttle_backend_unavailable"]
    assert warnings == [
        {"event": "throttle_backend_unavailable", "scope": "anon", "log_level": "warning"}
    ]
    for raw in ("203.0.113.7", "10.0.0.5", pii_hmac("203.0.113.7"), "throttle_anon"):
        assert raw not in repr(logs)


@pytest.mark.urls("shared.tests.api_urls")
@pytest.mark.usefixtures("cache_down")
def test_cache_down_allows_authenticated_request() -> None:
    client = APIClient()
    user: Any = SimpleNamespace(pk=42, is_authenticated=True)
    client.force_authenticate(user=user)

    with capture_logs() as logs:
        response = client.get("/items")

    assert response.status_code == 200
    warnings = [log for log in logs if log["event"] == "throttle_backend_unavailable"]
    assert warnings == [
        {"event": "throttle_backend_unavailable", "scope": "account", "log_level": "warning"}
    ]
    assert "throttle_account_42" not in repr(logs)
