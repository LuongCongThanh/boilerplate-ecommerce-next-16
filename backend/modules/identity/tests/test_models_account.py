import importlib
import pkgutil

import pytest
from django.apps import apps
from django.db import IntegrityError, connection
from django.db.migrations.loader import MigrationLoader
from django.db.migrations.operations import CreateModel
from django.utils import timezone

import config.settings
from modules.identity.models import Account
from modules.identity.tests.factories import AccountFactory


@pytest.mark.django_db
def test_initial_migration_creates_identity_account() -> None:
    initial = MigrationLoader(connection).get_migration("modules", "0001_initial")
    created = [
        operation.options.get("db_table")
        for operation in initial.operations
        if isinstance(operation, CreateModel)
    ]

    assert created == ["identity_account"]
    assert "identity_account" in connection.introspection.table_names()


@pytest.mark.django_db
def test_email_unique_ignores_case() -> None:
    AccountFactory(email="lan@example.com")
    duplicate = AccountFactory.build(email="LAN@Example.com")

    with pytest.raises(IntegrityError, match="identity_account_email_lower_uniq"):
        duplicate.save()


def test_manager_normalizes_email_to_lowercase() -> None:
    normalized = Account.objects.normalize_email("  Lan@Example.COM ")

    assert normalized == "lan@example.com"


@pytest.mark.django_db
def test_anonymized_account_must_be_inactive() -> None:
    account = AccountFactory.build(anonymized_at=timezone.now(), is_active=True)

    with pytest.raises(IntegrityError, match="identity_account_anonymized_inactive"):
        account.save()


@pytest.mark.django_db
def test_unknown_kind_rejected_by_db() -> None:
    account = AccountFactory.build(kind="superuser")

    with pytest.raises(IntegrityError, match="identity_account_kind_valid"):
        account.save()


@pytest.mark.django_db
def test_unknown_language_rejected_by_db() -> None:
    account = AccountFactory.build(language="fr")

    with pytest.raises(IntegrityError, match="identity_account_language_valid"):
        account.save()


@pytest.mark.django_db
def test_no_django_auth_tables_after_migrate() -> None:
    tables = connection.introspection.table_names()

    django_auth_tables = [t for t in tables if t.startswith("auth_") or t == "django_admin_log"]
    assert django_auth_tables == []


def test_django_admin_not_installed_in_any_settings() -> None:
    # Không dùng Django Admin ở mọi môi trường (ADR 0004, 08 mục 2.4)
    settings_modules = [
        importlib.import_module(f"config.settings.{module.name}")
        for module in pkgutil.iter_modules(config.settings.__path__)
    ]

    with_admin = [
        module.__name__
        for module in settings_modules
        if "django.contrib.admin" in module.INSTALLED_APPS
    ]
    assert len(settings_modules) >= 4
    assert with_admin == []
    assert not apps.is_installed("django.contrib.admin")
