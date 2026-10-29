"""Đọc và kiểm tra biến môi trường (08 mục 2.3).

Mỗi biến được khai báo ở mốc đầu tiên dùng tới nó; `.env.example` chỉ chứa biến đã khai báo.
"""

from functools import lru_cache
from pathlib import Path
from urllib.parse import unquote, urlsplit

from django.core.exceptions import ImproperlyConfigured
from pydantic import SecretStr, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Env(BaseSettings):
    # extra="forbid": biến lạ hoặc gõ sai tên trong .env bị báo ngay, không bị bỏ qua êm
    model_config = SettingsConfigDict(extra="forbid")

    # Từ M0
    DJANGO_SETTINGS_MODULE: str = "config.settings.local"
    DJANGO_SECRET_KEY: SecretStr
    DATABASE_URL: str
    # Chỉ Compose dùng; khai báo để pydantic-settings không báo biến thừa khi đọc .env
    PG_PORT: int = 5432
    REDIS_URL: str
    EMAIL_HOST: str
    EMAIL_PORT: int
    PII_HMAC_KEYS: SecretStr
    STOREFRONT_ORIGIN: str
    BFF_SHARED_SECRET: SecretStr


def load_env(env_file: Path | None = BASE_DIR / ".env") -> Env:
    try:
        return Env(_env_file=env_file)  # type: ignore[call-arg]
    except ValidationError as exc:
        names = ", ".join(str(err["loc"][0]) for err in exc.errors() if err["loc"])
        raise ImproperlyConfigured(f"Thiếu hoặc sai biến môi trường: {names}") from exc


@lru_cache(maxsize=1)
def get_env() -> Env:
    return load_env()


def database_config(url: str) -> dict[str, object]:
    """Chuyển `postgres://user:pass@host:port/name` thành một mục của `DATABASES`."""
    parts = urlsplit(url)
    if parts.scheme not in {"postgres", "postgresql"}:
        raise ImproperlyConfigured("DATABASE_URL phải bắt đầu bằng postgres://")
    return {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": unquote(parts.path.lstrip("/")),
        "USER": unquote(parts.username or ""),
        "PASSWORD": unquote(parts.password or ""),
        "HOST": parts.hostname or "",
        "PORT": str(parts.port or 5432),
    }
