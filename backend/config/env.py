"""Đọc và kiểm tra biến môi trường (08 mục 2.3).

Mỗi biến được khai báo ở mốc đầu tiên dùng tới nó; `.env.example` chỉ chứa biến đã khai báo.
"""

from functools import lru_cache
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, unquote, urlsplit

from django.core.exceptions import ImproperlyConfigured
from pydantic import SecretStr, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Env(BaseSettings):
    # extra="forbid": biến lạ hoặc gõ sai tên trong .env bị báo ngay, không bị bỏ qua êm
    model_config = SettingsConfigDict(extra="forbid")

    # Từ M0
    # Không dùng để chọn settings: lúc đọc .env thì settings đã được chọn. Khai báo để .env
    # chứa được biến này, vì Compose nạp .env vào biến môi trường của container; chạy trên
    # máy thì đặt bằng `export` hoặc dùng mặc định `local` của manage.py
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

    @field_validator("PII_HMAC_KEYS")
    @classmethod
    def _check_keyring(cls, value: SecretStr) -> SecretStr:
        parse_keyring(value.get_secret_value())
        return value


def parse_keyring(raw: str) -> tuple[tuple[str, str], ...]:
    """Đọc keyring dạng `kid2:secret2,kid1:secret1` thành các cặp `(kid, secret)`.

    Khoá đầu dùng cho giá trị mới; khoá sau giữ để kiểm tra giá trị cũ (ADR 0016).
    Thông báo lỗi không chứa secret.
    """
    keys: list[tuple[str, str]] = []
    for entry in raw.split(","):
        kid, sep, secret = entry.strip().partition(":")
        if not sep or not kid or not secret:
            raise ValueError("mỗi khoá phải có dạng kid:secret, kid và secret không rỗng")
        if any(kid == seen for seen, _ in keys):
            raise ValueError(f"kid {kid!r} bị trùng")
        keys.append((kid, secret))
    return tuple(keys)


def load_env(env_file: Path | None = BASE_DIR / ".env") -> Env:
    try:
        return Env(_env_file=env_file)  # type: ignore[call-arg]
    except ValidationError as exc:
        names = ", ".join(str(err["loc"][0]) for err in exc.errors() if err["loc"])
        raise ImproperlyConfigured(f"Thiếu hoặc sai biến môi trường: {names}") from exc


@lru_cache(maxsize=1)
def get_env() -> Env:
    return load_env()


def database_config(url: str) -> dict[str, Any]:
    """Chuyển `postgres://user:pass@host:port/name?opt=v` thành một mục của `DATABASES`.

    Tham số query (ví dụ `sslmode=require` cho RDS) được giữ lại trong `OPTIONS`.
    """
    parts = urlsplit(url)
    if parts.scheme not in {"postgres", "postgresql"}:
        raise ImproperlyConfigured("DATABASE_URL phải bắt đầu bằng postgres://")
    try:
        port = parts.port or 5432
    except ValueError as exc:
        raise ImproperlyConfigured("DATABASE_URL có port không hợp lệ") from exc
    return {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": unquote(parts.path.lstrip("/")),
        "USER": unquote(parts.username or ""),
        "PASSWORD": unquote(parts.password or ""),
        "HOST": parts.hostname or "",
        "PORT": str(port),
        "OPTIONS": dict(parse_qsl(parts.query)),
    }
