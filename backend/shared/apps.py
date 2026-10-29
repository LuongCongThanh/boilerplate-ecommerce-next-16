from django.apps import AppConfig


class SharedConfig(AppConfig):
    name = "shared"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self) -> None:
        from shared import checks  # noqa: F401  # đăng ký system check
