import copy
from typing import Any

import pytest
from django.conf import settings
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings

# Ghi đè DATABASES là cố ý: trỏ lệnh tới DB không tồn tại để không chạm database thật
pytestmark = pytest.mark.filterwarnings("ignore:Overriding setting DATABASES")


def _databases(host: str) -> dict[str, Any]:
    # Port 1 không có PostgreSQL: lệnh bỏ qua kiểm tra mà nối DB thì lỗi kết nối, không phải
    # CommandError, nên test đỏ mà không chạm vào database thật
    databases = copy.deepcopy(settings.DATABASES)
    databases["default"].update(HOST=host, PORT="1", NAME="reset_db_guard")
    return databases


def test_refuses_when_debug_is_off() -> None:
    with (
        override_settings(DEBUG=False, DATABASES=_databases("localhost")),
        pytest.raises(CommandError, match="DEBUG"),
    ):
        call_command("reset_db")


@pytest.mark.parametrize("host", ["db.example.com", "fashion.abc123.rds.amazonaws.com", ""])
def test_refuses_non_local_database_host(host: str) -> None:
    with (
        override_settings(DEBUG=True, DATABASES=_databases(host)),
        pytest.raises(CommandError, match="localhost"),
    ):
        call_command("reset_db")
