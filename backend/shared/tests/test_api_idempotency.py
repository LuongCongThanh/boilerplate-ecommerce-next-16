import hashlib
import json
import threading
from collections.abc import Iterator
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

import pytest
import time_machine
from django.db import connection, transaction
from rest_framework.test import APIClient

from shared.api.idempotency import LEASE, Claim, LeaseLost
from shared.models import IdempotencyKey, IdempotencyStatus, uuid7
from shared.testing.factories import IdempotencyKeyFactory
from shared.tests._helpers import error_of
from shared.tests.api_urls import IdempotentEffect, OutOfStock

pytestmark = pytest.mark.urls("shared.tests.api_urls")

URL = "/idempotent/FS2610-7K3QZD/"
KEY = "0192f3a4-5b6c-7d8e-9f01-23456789abcd"
CART_TOKEN = "cart-token-a"
# Scope mà `begin` dựng cho `post(...)` mặc định
SCOPE = f"POST /idempotent/FS2610-7K3QZD|cart:{hashlib.sha256(CART_TOKEN.encode()).hexdigest()}"
NOW = datetime(2026, 10, 30, 8, 0, tzinfo=UTC)


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


def in_progress_key(body: dict[str, Any], **kwargs: Any) -> IdempotencyKey:
    """Key mà một worker khác đang giữ cho `post(body)`."""
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return IdempotencyKeyFactory.create(
        scope=SCOPE, key=KEY, request_hash=hashlib.sha256(canonical.encode()).hexdigest(), **kwargs
    )


def claim_of(row: IdempotencyKey) -> Claim:
    """`Claim` mà worker đang giữ `row` đã nhận từ `begin`."""
    assert row.lease_token is not None
    return Claim(key_id=row.pk, operation_id=row.operation_id, lease_token=row.lease_token)


def test_in_progress_key_returns_pending_with_retry_after() -> None:
    in_progress_key({"note": "a"})

    response = post({"note": "a"})

    assert response.status_code == 202
    assert response.json() == {"code": "IDEMPOTENCY_IN_PROGRESS", "retry_after": 3}
    assert response.headers["Retry-After"] == "3"
    assert IdempotentEffect.objects.count() == 0


def test_different_body_conflicts_even_while_in_progress() -> None:
    in_progress_key({"note": "a"})

    response = post({"note": "b"})

    assert response.status_code == 409
    assert error_of(response)["code"] == "IDEMPOTENCY_CONFLICT"
    assert IdempotentEffect.objects.count() == 0


def test_expired_lease_is_taken_over() -> None:
    with time_machine.travel(NOW, tick=False) as traveller:
        stale = in_progress_key({"note": "a"})
        traveller.shift(LEASE)

        response = post({"note": "a"})

    assert response.status_code == 201
    assert response.json()["operation_id"] == str(stale.operation_id)
    assert IdempotentEffect.objects.count() == 1
    stale.refresh_from_db()
    assert stale.status == IdempotencyStatus.COMPLETED


def finish_with_effect(claim: Claim) -> None:
    """Tác động nghiệp vụ của worker giữ `claim`, viết như view: ghi tác động rồi lưu kết quả."""
    with claim, transaction.atomic():
        IdempotentEffect.objects.create(note="stale")
        claim.complete(201, {"note": "stale"})


def test_stale_lease_complete_rolls_back_effect() -> None:
    with time_machine.travel(NOW, tick=False) as traveller:
        stale = in_progress_key({"note": "a"})
        old_worker = claim_of(stale)
        traveller.shift(LEASE)
        taken_over = post({"note": "a"})

        with pytest.raises(LeaseLost):
            finish_with_effect(old_worker)

    assert IdempotentEffect.objects.get().note == "a"
    stale.refresh_from_db()
    assert stale.response_body == taken_over.json()


def test_business_rollback_leaves_key_not_completed() -> None:
    body = {"note": "a", "fail_after_effect": True}

    first = post(body)
    retry = post(body)

    assert first.status_code == 409
    assert error_of(first)["code"] == "OUT_OF_STOCK"
    # Gửi lại cùng key chạy lại từ đầu, không nhận 202 hay kết quả lỗi đã lưu
    assert error_of(retry)["code"] == "OUT_OF_STOCK"
    assert IdempotentEffect.objects.count() == 0
    assert not IdempotencyKey.objects.exists()


def fail_after_effect(claim: Claim) -> None:
    with claim, transaction.atomic():
        IdempotentEffect.objects.create(note="a")
        raise OutOfStock


def test_rollback_keeps_key_with_resource_id() -> None:
    # Payment đã gắn vào key trước khi gọi gateway: luồng khôi phục cần dòng này
    attached = in_progress_key({"note": "a"}, resource_id=uuid7())
    claim = claim_of(attached)

    with pytest.raises(OutOfStock):
        fail_after_effect(claim)

    assert IdempotencyKey.objects.filter(pk=attached.pk).exists()
    assert IdempotentEffect.objects.count() == 0


@pytest.mark.django_db(transaction=True)
def test_concurrent_same_key_runs_effect_once(monkeypatch: pytest.MonkeyPatch) -> None:
    responded = threading.Event()
    complete = Claim.complete

    def complete_after_other_responds(claim: Claim, *args: Any, **kwargs: Any) -> None:
        # Bên giữ key chỉ lưu kết quả sau khi bên kia đã nhận response, để bên kia thấy
        # key còn `in_progress` chứ không phải kết quả đã lưu
        responded.wait(timeout=5)
        complete(claim, *args, **kwargs)

    monkeypatch.setattr(Claim, "complete", complete_after_other_responds)
    barrier = threading.Barrier(2)
    responses: list[Any] = []
    errors: list[BaseException] = []

    def run() -> None:
        try:
            barrier.wait()
            responses.append(post({"note": "a"}))
            responded.set()
        except BaseException as exc:
            errors.append(exc)
        finally:
            connection.close()

    threads = [threading.Thread(target=run) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert errors == []
    statuses = sorted(response.status_code for response in responses)
    assert statuses == [201, 202]
    created = next(response for response in responses if response.status_code == 201)
    assert IdempotentEffect.objects.count() == 1
    assert created.json()["operation_id"] == str(IdempotencyKey.objects.get().operation_id)
