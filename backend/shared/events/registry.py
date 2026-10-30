"""Registry class sự kiện và handler (07 mục 1, 2).

Class sự kiện đăng ký theo `(event_type, schema_version)` khi được import; handler đăng ký bằng
`@handles`. Trùng khoá ném lỗi ngay khi import để lỗi cấu hình không chờ tới lúc chạy.
"""

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from django.core.exceptions import ImproperlyConfigured

if TYPE_CHECKING:
    from shared.events.base import DomainEvent


@dataclass(frozen=True)
class Handler:
    # `name` là cột `handler` của delivery: ổn định khi đổi tên file/hàm
    name: str
    event_type: str
    version: int
    func: Callable[[Any], None]


class Registry:
    def __init__(self) -> None:
        self._events: dict[tuple[str, int], type[DomainEvent]] = {}
        self._handlers: dict[str, Handler] = {}

    def register_event(self, event_class: type[DomainEvent]) -> None:
        key = (event_class.event_type, event_class.schema_version)
        existing = self._events.get(key)
        if existing is not None:
            raise ImproperlyConfigured(
                f"Sự kiện {key[0]} v{key[1]} đã đăng ký bởi "
                f"{existing.__module__}.{existing.__qualname__}"
            )
        self._events[key] = event_class

    def register_handler(self, handler: Handler) -> None:
        existing = self._handlers.get(handler.name)
        if existing is not None:
            raise ImproperlyConfigured(
                f"Handler {handler.name} đã đăng ký bởi "
                f"{existing.func.__module__}.{existing.func.__qualname__}"
            )
        self._handlers[handler.name] = handler

    def get_event_class(self, event_type: str, version: int) -> type[DomainEvent] | None:
        return self._events.get((event_type, version))

    def event_classes(self) -> list[type[DomainEvent]]:
        return list(self._events.values())

    def get_handler(self, name: str) -> Handler | None:
        return self._handlers.get(name)

    def handlers_for(self, event_type: str, version: int) -> list[Handler]:
        return [
            handler
            for handler in self._handlers.values()
            if handler.event_type == event_type and handler.version == version
        ]

    @contextmanager
    def isolated(self) -> Iterator[None]:
        """Khôi phục registry khi thoát, cho test khai báo sự kiện/handler tạm."""
        events, handlers = dict(self._events), dict(self._handlers)
        try:
            yield
        finally:
            self._events, self._handlers = events, handlers


registry = Registry()


def handles[F: Callable[[Any], None]](
    event_type: str, version: int = 1, *, name: str
) -> Callable[[F], F]:
    """Đăng ký hàm làm handler của `event_type` ở `version`.

    `name` có dạng `<module>.<snake_case>` như tên Celery task (02 mục 9.2). Handler nhận
    instance của class sự kiện đã parse từ payload.
    """

    def decorator(func: F) -> F:
        registry.register_handler(Handler(name, event_type, version, func))
        return func

    return decorator
