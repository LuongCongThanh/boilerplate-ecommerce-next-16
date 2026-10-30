"""Ghi sự kiện vào outbox trong transaction hiện tại (07 mục 1.1.1, ADR 0007)."""

from shared.events.base import DomainEvent
from shared.events.models import OutboxEvent


class EventPublisher:
    """Chỗ cắm adapter khác (ví dụ Kafka, ADR 0007); bản mặc định chỉ ghi outbox."""

    def publish(self, event: DomainEvent) -> OutboxEvent:
        # Không tự mở transaction: sự kiện phải commit/rollback cùng dữ liệu nghiệp vụ của
        # bên gọi
        return OutboxEvent.objects.create(
            id=event.event_id,
            event_type=event.event_type,
            schema_version=event.schema_version,
            payload=event.to_payload(),
            occurred_at=event.occurred_at,
        )


_default_publisher = EventPublisher()


def publish(event: DomainEvent) -> OutboxEvent:
    return _default_publisher.publish(event)
