"""Factory của identity (02 mục 9.5, 12 mục 4)."""

from typing import Any

import factory
from factory.django import DjangoModelFactory

from modules.identity.constants import AccountKind
from modules.identity.models import Account

DEFAULT_PASSWORD = "Fashion-Store-2026"


class AccountFactory(DjangoModelFactory[Account]):
    """Tài khoản Staff đang hoạt động; trait `admin` cho Admin."""

    class Meta:
        model = Account
        skip_postgeneration_save = True

    email = factory.Sequence(lambda n: f"staff{n}@example.com")
    kind = AccountKind.STAFF

    class Params:
        admin = factory.Trait(kind=AccountKind.ADMIN)

    @factory.post_generation
    def password(self: Account, create: bool, extracted: str | None, **kwargs: Any) -> None:
        self.set_password(extracted or DEFAULT_PASSWORD)
        if create:
            self.save(update_fields=["password"])
