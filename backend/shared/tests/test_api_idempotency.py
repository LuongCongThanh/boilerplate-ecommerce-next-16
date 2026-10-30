from collections.abc import Iterator
from types import SimpleNamespace
from typing import Any

import pytest
from django.db import connection
from rest_framework.test import APIClient

from shared.tests._helpers import error_of
from shared.tests.api_urls import IdempotentEffect

pytestmark = pytest.mark.urls("shared.tests.api_urls")

URL = "/idempotent/FS2610-7K3QZD/"
KEY = "0192f3a4-5b6c-7d8e-9f01-23456789abcd"
CART_TOKEN = "cart-token-a"


@pytest.fixture(autouse=True)
def effect_table(db: None) -> Iterator[None]:
    # Model chỉ dùng trong test, không có migration
    with connection.schema_editor() as editor:
        editor.create_model(IdempotentEffect)
    yield
    with connection.schema_editor() as editor:
        editor.delete_model(IdempotentEffect)


def post(
    body: dict[str, Any],
    *,
    key: str | None = KEY,
    cart_token: str | None = CART_TOKEN,
    client: APIClient | None = None,
) -> Any:
    headers: dict[str, str] = {}
    if key is not None:
        headers["Idempotency-Key"] = key
    if cart_token is not None:
        headers["X-Cart-Token"] = cart_token
    return (client or APIClient()).post(URL, body, format="json", headers=headers)


def account_client(pk: int) -> APIClient:
    client = APIClient()
    user: Any = SimpleNamespace(pk=pk, is_authenticated=True)
    client.force_authenticate(user=user)
    return client


def test_same_key_same_body_replays_saved_response_without_rerun() -> None:
    first = post({"note": "a"})
    second = post({"note": "a"})

    assert first.status_code == 201
    assert second.status_code == 201
    assert second.json() == first.json()
    assert IdempotentEffect.objects.count() == 1


def test_body_key_order_does_not_change_request_hash() -> None:
    first = post({"note": "a", "quantity": 2})
    second = post({"quantity": 2, "note": "a"})

    assert second.status_code == 201
    assert second.json() == first.json()
    assert IdempotentEffect.objects.count() == 1


def test_same_key_different_body_returns_idempotency_conflict() -> None:
    post({"note": "a"})

    response = post({"note": "b"})

    assert response.status_code == 409
    assert error_of(response)["code"] == "IDEMPOTENCY_CONFLICT"
    assert IdempotentEffect.objects.count() == 1


def test_same_key_different_account_does_not_see_other_result() -> None:
    first = post({"note": "a"}, cart_token=None, client=account_client(1))
    second = post({"note": "a"}, cart_token=None, client=account_client(2))

    assert second.status_code == 201
    assert second.json()["effect_id"] != first.json()["effect_id"]
    assert IdempotentEffect.objects.count() == 2


def test_same_key_different_cart_token_does_not_see_other_result() -> None:
    first = post({"note": "a"}, cart_token="cart-token-a")
    second = post({"note": "a"}, cart_token="cart-token-b")

    assert second.status_code == 201
    assert second.json()["effect_id"] != first.json()["effect_id"]
    assert IdempotentEffect.objects.count() == 2


def test_request_without_identity_returns_validation_error() -> None:
    response = post({"note": "a"}, cart_token=None)

    assert response.status_code == 400
    error = error_of(response)
    assert error["code"] == "VALIDATION_ERROR"
    assert set(error["details"]["fields"]) == {"X-Cart-Token"}
    assert IdempotentEffect.objects.count() == 0


def test_missing_key_returns_validation_error() -> None:
    response = post({"note": "a"}, key=None)

    assert response.status_code == 400
    error = error_of(response)
    assert error["code"] == "VALIDATION_ERROR"
    assert set(error["details"]["fields"]) == {"Idempotency-Key"}
    assert IdempotentEffect.objects.count() == 0


def test_non_uuid_key_returns_validation_error() -> None:
    response = post({"note": "a"}, key="order-1")

    assert response.status_code == 400
    error = error_of(response)
    assert error["code"] == "VALIDATION_ERROR"
    assert set(error["details"]["fields"]) == {"Idempotency-Key"}
    assert IdempotentEffect.objects.count() == 0
