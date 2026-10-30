from collections.abc import Iterator

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from structlog.testing import capture_logs

from modules.identity.constants import AccountKind
from modules.identity.models import Account
from modules.identity.tests.factories import DEFAULT_PASSWORD, AccountFactory
from modules.management.commands import create_staff

pytestmark = pytest.mark.django_db


def _type_passwords(monkeypatch: pytest.MonkeyPatch, *passwords: str) -> None:
    """Giả hai lần nhập mật khẩu qua getpass, theo thứ tự."""
    answers: Iterator[str] = iter(passwords)
    monkeypatch.setattr(create_staff, "getpass", lambda prompt="": next(answers))


def test_create_staff_admin_creates_admin_account(monkeypatch: pytest.MonkeyPatch) -> None:
    # Không truyền --email: lệnh hỏi email qua input()
    monkeypatch.setattr(create_staff, "input", lambda prompt="": "Boss@Example.com", raising=False)
    _type_passwords(monkeypatch, DEFAULT_PASSWORD, DEFAULT_PASSWORD)

    with capture_logs() as logs:
        call_command("create_staff", "--admin", "--full-name", "Trần Chủ")

    account = Account.objects.get()
    assert account.email == "boss@example.com"
    assert account.kind == AccountKind.ADMIN
    assert account.full_name == "Trần Chủ"
    assert account.check_password(DEFAULT_PASSWORD)
    created = [log for log in logs if log["event"] == "staff_account_created"]
    assert created == [
        {
            "event": "staff_account_created",
            "log_level": "info",
            "account_id": account.id,
            "kind": AccountKind.ADMIN,
        }
    ]


def test_create_staff_same_email_raises_command_error(monkeypatch: pytest.MonkeyPatch) -> None:
    AccountFactory(email="staff@example.com")
    _type_passwords(monkeypatch, DEFAULT_PASSWORD, DEFAULT_PASSWORD)

    with pytest.raises(CommandError, match="Email đã được dùng"):
        call_command("create_staff", "--email", "Staff@Example.com")

    assert Account.objects.count() == 1


@pytest.mark.parametrize(
    "password",
    [
        "Ab1-xyz",  # ngắn hơn 8 ký tự
        "password123",  # mật khẩu phổ biến
        "20261030123",  # toàn số
        "an.nguyen.example",  # giống email
        "nguyenvanan",  # giống họ tên
    ],
)
def test_create_staff_rejects_weak_password(monkeypatch: pytest.MonkeyPatch, password: str) -> None:
    _type_passwords(monkeypatch, password, password)

    with pytest.raises(CommandError, match="Mật khẩu chưa đủ mạnh"):
        call_command(
            "create_staff", "--email", "an.nguyen@example.com", "--full-name", "Nguyen Van An"
        )

    assert not Account.objects.exists()


def test_create_staff_rejects_mismatched_password(monkeypatch: pytest.MonkeyPatch) -> None:
    _type_passwords(monkeypatch, DEFAULT_PASSWORD, DEFAULT_PASSWORD + "x")

    with pytest.raises(CommandError, match="không khớp"):
        call_command("create_staff", "--email", "an.nguyen@example.com")

    assert not Account.objects.exists()
