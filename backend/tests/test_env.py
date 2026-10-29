from pathlib import Path

import pytest
from django.core.exceptions import ImproperlyConfigured

from config.env import Env, load_env

M0_VARS = {
    "DJANGO_SECRET_KEY": "test-secret",
    "DATABASE_URL": "postgres://fashion:fashion@localhost:5432/fashion",
    "REDIS_URL": "redis://localhost:6379/0",
    "EMAIL_HOST": "localhost",
    "EMAIL_PORT": "1025",
    "PII_HMAC_KEYS": "test-pii-1:test-pii-secret",
    "STOREFRONT_ORIGIN": "http://localhost:3000",
    "BFF_SHARED_SECRET": "test-bff-secret",
}


@pytest.fixture
def m0_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in Env.model_fields:
        monkeypatch.delenv(name, raising=False)
    for name, value in M0_VARS.items():
        monkeypatch.setenv(name, value)


@pytest.mark.usefixtures("m0_env")
def test_loads_with_only_m0_variables() -> None:
    env = load_env(env_file=None)

    assert env.EMAIL_PORT == 1025


@pytest.mark.usefixtures("m0_env")
def test_missing_required_variable_names_it(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("BFF_SHARED_SECRET")

    with pytest.raises(ImproperlyConfigured, match="BFF_SHARED_SECRET"):
        load_env(env_file=None)


@pytest.mark.usefixtures("m0_env")
def test_parses_keyring_once_and_hides_secrets(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PII_HMAC_KEYS", "k2:secret-2,k1:secret-1")

    env = load_env(env_file=None)

    assert [(kid, secret.get_secret_value()) for kid, secret in env.PII_HMAC_KEYS] == [
        ("k2", "secret-2"),
        ("k1", "secret-1"),
    ]
    assert "secret-2" not in repr(env)


@pytest.mark.usefixtures("m0_env")
def test_malformed_keyring_names_variable_without_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PII_HMAC_KEYS", "k1:top-secret,k1:other")

    with pytest.raises(ImproperlyConfigured, match="PII_HMAC_KEYS") as exc_info:
        load_env(env_file=None)

    assert "top-secret" not in str(exc_info.value)


@pytest.mark.usefixtures("m0_env")
def test_bff_secret_accepts_two_values_for_rotation(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BFF_SHARED_SECRET", "new-secret, old-secret")

    env = load_env(env_file=None)

    assert [secret.get_secret_value() for secret in env.BFF_SHARED_SECRET] == [
        "new-secret",
        "old-secret",
    ]
    assert "new-secret" not in repr(env)


@pytest.mark.parametrize("raw", ["", " , ", "a,,b", "a,b,c"])
@pytest.mark.usefixtures("m0_env")
def test_bff_secret_rejects_empty_or_more_than_two_values(
    monkeypatch: pytest.MonkeyPatch, raw: str
) -> None:
    monkeypatch.setenv("BFF_SHARED_SECRET", raw)

    with pytest.raises(ImproperlyConfigured, match="BFF_SHARED_SECRET") as exc_info:
        load_env(env_file=None)

    assert "a,b" not in str(exc_info.value)


@pytest.mark.usefixtures("m0_env")
def test_redis_port_is_accepted_and_defaults_to_6380(tmp_path: Path) -> None:
    # Compose đọc REDIS_PORT từ .env; extra="forbid" nên Env phải khai báo biến này
    env_file = tmp_path / ".env"
    env_file.write_text("REDIS_PORT=6390\n", encoding="utf-8")

    assert load_env(env_file=env_file).REDIS_PORT == 6390
    assert load_env(env_file=None).REDIS_PORT == 6380


@pytest.mark.usefixtures("m0_env")
def test_database_host_is_accepted_and_defaults_to_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Container trong Compose đặt DATABASE_HOST thay vì ghi DATABASE_URL có mật khẩu
    assert load_env(env_file=None).DATABASE_HOST == ""

    monkeypatch.setenv("DATABASE_HOST", "host.docker.internal")

    assert load_env(env_file=None).DATABASE_HOST == "host.docker.internal"
