from config.settings.base import *  # noqa: F403

DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0"]  # noqa: S104

# Mailpit (08 mục 2.3)
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
