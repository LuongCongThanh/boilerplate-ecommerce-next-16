"""Cấu hình chung mọi môi trường."""

from config.env import BASE_DIR, database_config, get_env

env = get_env()

SECRET_KEY = env.DJANGO_SECRET_KEY.get_secret_value()
DEBUG = False
ALLOWED_HOSTS: list[str] = []

# Không dùng django.contrib.admin, auth và sessions: không có Django Admin (ADR 0004),
# xác thực bằng JWT từ M1 (ADR 0002)
INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "rest_framework",
    "drf_spectacular",
    "django_celery_beat",
    "django_structlog",
    "shared",
    "modules",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django_structlog.middlewares.RequestMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {"default": database_config(env.DATABASE_URL)}
# Dùng connection pool của Django 5.2 thay cho kết nối giữ lâu (02 mục 3.1)
DATABASES["default"]["OPTIONS"] = {"pool": True}
DATABASES["default"]["CONN_MAX_AGE"] = 0
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": env.REDIS_URL,
    }
}

LANGUAGE_CODE = "vi"
LANGUAGES = [("vi", "Tiếng Việt"), ("en", "English")]
TIME_ZONE = "Asia/Ho_Chi_Minh"
USE_I18N = True
USE_TZ = True
LOCALE_PATHS = [BASE_DIR / "locale"]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {},
    }
]

EMAIL_HOST = env.EMAIL_HOST
EMAIL_PORT = env.EMAIL_PORT

REST_FRAMEWORK: dict[str, object] = {
    # Chưa có xác thực ở M0; JWT thêm ở M1
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": [],
    "UNAUTHENTICATED_USER": None,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Fashion Store API",
    "VERSION": "0.1.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

CELERY_BROKER_URL = env.REDIS_URL
CELERY_TASK_DEFAULT_QUEUE = "default"
CELERY_TIMEZONE = TIME_ZONE
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"

# Bật Swagger UI và schema; production tắt (04 mục 4.4)
API_DOCS_ENABLED = True
