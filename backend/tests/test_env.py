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
