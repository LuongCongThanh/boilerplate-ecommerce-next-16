"""Fixture cần Tài khoản (12 mục 4): `shared` không được import `modules.identity`."""

from typing import Any

import pytest
from rest_framework.test import APIClient

from modules.identity.models import Account
from modules.identity.tests.factories import AccountFactory

pytest_plugins = ["shared.testing.fixtures"]


def _backoffice_client(account: Account) -> APIClient:
    # Tạm giả claims của token back-office để qua IsStaff/IsAdmin; M1 thay bằng JWT thật.
    # Stub DRF đòi `Token` của authtoken nên khai báo `Any`
    claims: Any = {"aud": "backoffice"}
    client = APIClient()
    client.force_authenticate(user=account, token=claims)
    return client


@pytest.fixture
def staff_client(db: None) -> APIClient:
    """Client của một Staff."""
    return _backoffice_client(AccountFactory.create())


@pytest.fixture
def admin_client(db: None) -> APIClient:
    """Client của một Admin."""
    return _backoffice_client(AccountFactory.create(admin=True))
