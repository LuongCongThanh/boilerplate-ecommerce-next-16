from typing import Any

import pytest
from django.test import Client

API_URLS = pytest.mark.urls("shared.tests.api_urls")


def _error(response: Any) -> dict[str, Any]:
    body = response.json()
    assert set(body) == {"error"}
    error: dict[str, Any] = body["error"]
    assert set(error) == {"code", "message", "details", "request_id"}
    assert error["request_id"]
    assert error["message"]
    return error


def test_unknown_route_returns_error_dto(client: Client) -> None:
    # Dùng urlconf thật để kiểm handler404 khai báo ở config/urls.py
    response = client.get("/api/v1/khong-ton-tai")

    assert response.status_code == 404
    error = _error(response)
    assert (error["code"], error["details"]) == ("NOT_FOUND", {})


@API_URLS
def test_method_not_allowed_returns_error_dto(client: Client) -> None:
    response = client.post("/items")

    assert response.status_code == 405
    error = _error(response)
    assert (error["code"], error["details"]) == ("METHOD_NOT_ALLOWED", {})
    assert "GET" in response["Allow"]


@API_URLS
def test_validation_error_returns_fields(client: Client) -> None:
    response = client.post(
        "/validate",
        {"address": {"city": ""}, "lines": [{"sku": "A"}, {}]},
        content_type="application/json",
    )

    assert response.status_code == 400
    error = _error(response)
    assert error["code"] == "VALIDATION_ERROR"
    assert set(error["details"]["fields"]) == {"name", "address.city", "lines.1.sku"}
    assert all(isinstance(m, str) for m in error["details"]["fields"]["address.city"])


@API_URLS
def test_domain_error_uses_class_status(client: Client) -> None:
    response = client.get("/domain-error")

    assert response.status_code == 409
    error = _error(response)
    assert error["code"] == "OUT_OF_STOCK"
    assert error["message"] == "Một số sản phẩm không đủ hàng."
    assert error["details"] == {"items": [{"sku": "A", "requested": 3, "available": 1}]}


@API_URLS
def test_throttled_keeps_retry_after_header(client: Client) -> None:
    response = client.get("/throttled")

    assert response.status_code == 429
    assert _error(response)["code"] == "THROTTLED"
    assert response["Retry-After"] == "30"


@API_URLS
def test_unhandled_exception_returns_internal_error() -> None:
    client = Client(raise_request_exception=False)

    response = client.get("/boom")

    assert response.status_code == 500
    error = _error(response)
    assert (error["code"], error["details"]) == ("INTERNAL_ERROR", {})
    assert "secret internal detail" not in response.content.decode()


@API_URLS
def test_default_permission_denies_anonymous(client: Client) -> None:
    response = client.get("/private")

    assert response.status_code == 403
    assert _error(response)["code"] == "PERMISSION_DENIED"


def test_schema_is_public_despite_default_permission(client: Client) -> None:
    response = client.get("/api/schema/")

    assert response.status_code == 200
