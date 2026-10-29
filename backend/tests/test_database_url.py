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


def test_invalid_port_raises_improperly_configured() -> None:
    with pytest.raises(ImproperlyConfigured, match="port"):
        database_config("postgres://u:p@localhost:54x2/fashion")
