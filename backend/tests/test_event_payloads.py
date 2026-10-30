"""Payload sự kiện không chứa secret hay PII, xét theo tên field (07 mục 2, mục 5).

Đặt ở `backend/tests/` để thấy sự kiện của mọi module. Test chỉ bắt lỗi theo tên field;
reviewer vẫn phải đọc payload của mọi sự kiện mới.
"""

import importlib
import importlib.util
import pkgutil

import modules
from shared.events import DomainEvent
from shared.events.registry import registry

FORBIDDEN_SUBSTRINGS = ("email", "phone", "address", "name", "token", "password")


def forbidden_field_names(event_class: type[DomainEvent]) -> list[str]:
    return [
        field
        for field in event_class.model_fields
        if field.endswith("_url") or any(word in field for word in FORBIDDEN_SUBSTRINGS)
    ]


def _import_module_events() -> None:
    # Class sự kiện đăng ký khi được import; nạp events.py và handlers.py của mọi module con
    for module in pkgutil.iter_modules(modules.__path__, prefix="modules."):
        if not module.ispkg:
            continue
        for part in ("events", "handlers"):
            name = f"{module.name}.{part}"
            if importlib.util.find_spec(name) is not None:
                importlib.import_module(name)


def test_forbidden_field_names_detected() -> None:
    class LeakyV1(DomainEvent):
        order_code: str
        contact_name: str
        reset_token: str
        to_address: str
        avatar_url: str
        amount: int

    assert forbidden_field_names(LeakyV1) == [
        "contact_name",
        "reset_token",
        "to_address",
        "avatar_url",
    ]


def test_registered_event_payloads_have_no_pii() -> None:
    _import_module_events()

    leaks = {
        f"{cls.event_type} v{cls.schema_version}": names
        for cls in registry.event_classes()
        if (names := forbidden_field_names(cls))
    }

    assert leaks == {}
