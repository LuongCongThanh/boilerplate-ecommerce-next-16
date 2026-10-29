"""Đọc và kiểm tra biến môi trường (08 mục 2.3).

Mỗi biến được khai báo ở mốc đầu tiên dùng tới nó; `.env.example` chỉ chứa biến đã khai báo.
"""

from functools import lru_cache
from pathlib import Path
from typing import Annotated, Any
from urllib.parse import parse_qsl, unquote, urlsplit

from django.core.exceptions import ImproperlyConfigured
from pydantic import SecretStr, ValidationError, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

from shared.privacy import parse_keyring

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
    # Chỉ Compose dùng: cổng Redis của Compose mở ra máy, tránh 6379 của project khác
    REDIS_PORT: int = 6380
    REDIS_URL: str
    EMAIL_HOST: str
    EMAIL_PORT: int
    # Dạng `kid2:s2,kid1:s1`, không phải JSON: NoDecode để pydantic-settings không tự decode
    PII_HMAC_KEYS: Annotated[tuple[tuple[str, SecretStr], ...], NoDecode]
    STOREFRONT_ORIGIN: str
    # 1 hoặc 2 secret cách nhau bằng dấu phẩy để xoay không gián đoạn (05 mục 5)
    BFF_SHARED_SECRET: Annotated[tuple[SecretStr, ...], NoDecode]

    @field_validator("PII_HMAC_KEYS", mode="before")
    @classmethod
    def _parse_keyring(cls, value: object) -> object:
        if not isinstance(value, str):
            return value
        # Bọc secret trong SecretStr để repr của Env và lỗi validate không lộ secret
        return tuple((kid, SecretStr(secret)) for kid, secret in parse_keyring(value))

    @field_validator("BFF_SHARED_SECRET", mode="before")
    @classmethod
    def _parse_bff_secrets(cls, value: object) -> object:
        if not isinstance(value, str):
            return value
        secrets = [secret.strip() for secret in value.split(",")]
        # Thông báo lỗi không chứa secret
        if not 1 <= len(secrets) <= 2 or not all(secrets):
            raise ValueError("cần 1 hoặc 2 secret không rỗng, cách nhau bằng dấu phẩy")
        return tuple(SecretStr(secret) for secret in secrets)


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
