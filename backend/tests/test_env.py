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
