"""OpenAPI sinh bằng `manage.py spectacular`: component `ErrorDTO` và response lỗi mặc định
(04 mục 3, 5.1, 5.6)."""

from pathlib import Path
from typing import Any

import pytest
import yaml
from django.core.management import call_command

ERROR_DTO_REF = {"$ref": "#/components/schemas/ErrorDTO"}
WARDS_PATH = "/api/v1/store/geo/provinces/{code}/wards"
PROVINCES_PATH = "/api/v1/store/geo/provinces"


@pytest.fixture(scope="module")
def schema(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Any]:
    file = tmp_path_factory.mktemp("openapi") / "openapi.yaml"
    call_command("spectacular", "--validate", "--fail-on-warn", "--file", str(file))
    loaded: dict[str, Any] = yaml.safe_load(Path(file).read_text(encoding="utf-8"))
    return loaded


def _operations(schema: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    return [
        (f"{method.upper()} {path}", operation)
        for path, item in schema["paths"].items()
        for method, operation in item.items()
    ]


def _error_ref(response: dict[str, Any]) -> dict[str, Any]:
    schema: dict[str, Any] = response["content"]["application/json"]["schema"]
    return schema


def test_schema_has_error_dto_component(schema: dict[str, Any]) -> None:
    error_dto = schema["components"]["schemas"]["ErrorDTO"]
    body = error_dto["properties"]["error"]

    assert error_dto["required"] == ["error"]
    assert body["type"] == "object"
    assert body["required"] == ["code", "message", "details", "request_id"]
    assert body["properties"]["code"]["type"] == "string"
    assert body["properties"]["message"]["type"] == "string"
    assert body["properties"]["details"]["type"] == "object"
    assert body["properties"]["request_id"]["type"] == "string"


def test_every_operation_declares_common_errors(schema: dict[str, Any]) -> None:
    operations = _operations(schema)

    assert operations
    for name, operation in operations:
        responses = operation["responses"]
        for code in ("400", "429", "500"):
            assert _error_ref(responses[code]) == ERROR_DTO_REF, f"{name} {code}"
        assert list(responses) == sorted(responses), name


def test_operation_with_path_parameter_declares_404(schema: dict[str, Any]) -> None:
    wards = schema["paths"][WARDS_PATH]["get"]["responses"]
    provinces = schema["paths"][PROVINCES_PATH]["get"]["responses"]

    assert _error_ref(wards["404"]) == ERROR_DTO_REF
    assert "404" not in provinces
