from types import SimpleNamespace
from typing import Any

from rest_framework.request import Request
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework.views import APIView

from shared.api.throttling import AccountThrottle, AnonThrottle


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
