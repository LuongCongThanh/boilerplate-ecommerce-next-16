import pytest
from django.core.exceptions import ImproperlyConfigured

from config.env import database_config


def test_keeps_query_parameters_as_options() -> None:
    config = database_config("postgres://u:p@rds-host:5432/fashion?sslmode=require")

    assert config["OPTIONS"] == {"sslmode": "require"}
    assert config["HOST"] == "rds-host"


def test_allows_url_without_password() -> None:
    config = database_config("postgres://fashion@localhost:5432/fashion")

    assert config["USER"] == "fashion"
    assert config["PASSWORD"] == ""


def test_host_argument_overrides_host_of_url() -> None:
    # Compose chỉ đặt DATABASE_HOST, user và mật khẩu vẫn lấy từ DATABASE_URL của .env
    url = "postgres://fashion:secret@localhost:5433/fashion"

    config = database_config(url, host="host.docker.internal")

    assert config["HOST"] == "host.docker.internal"
    assert (config["USER"], config["PASSWORD"], config["PORT"]) == ("fashion", "secret", "5433")
    assert database_config(url, host="")["HOST"] == "localhost"


def test_invalid_port_raises_improperly_configured() -> None:
    with pytest.raises(ImproperlyConfigured, match="port"):
        database_config("postgres://u:p@localhost:54x2/fashion")
