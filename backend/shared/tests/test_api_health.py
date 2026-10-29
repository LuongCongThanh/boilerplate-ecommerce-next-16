import pytest
from django.db import DatabaseError
from django.test import Client


def test_healthz_returns_ok(client: Client) -> None:
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.django_db
def test_readyz_returns_ok_when_database_reachable(client: Client) -> None:
    response = client.get("/readyz")

    assert response.status_code == 200


@pytest.mark.django_db
def test_readyz_returns_503_when_database_unreachable(
    client: Client, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail(*args: object, **kwargs: object) -> None:
        raise DatabaseError("connection refused")

    monkeypatch.setattr("django.db.backends.utils.CursorWrapper.execute", fail)

    response = client.get("/readyz")

    assert response.status_code == 503
