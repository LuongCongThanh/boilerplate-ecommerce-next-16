from django.db import models


class AccountKind(models.TextChoices):
    CUSTOMER = "customer"
    STAFF = "staff"
    ADMIN = "admin"


class Language(models.TextChoices):
    VI = "vi"
    EN = "en"
