from datetime import UTC, datetime, timedelta

import pytest
import time_machine
from django.core.management import call_command
from django.core.management.base import CommandError
from structlog.testing import capture_logs

from shared.events import handles
from shared.events.consumer import process_delivery
from shared.events.models import DeliveryStatus, EventDelivery
from shared.events.tests.conftest import SampleHappenedV1
from shared.testing.factories import EventDeliveryFactory, OutboxEventFactory

pytestmark = pytest.mark.django_db

NOW = datetime(2026, 10, 30, 8, 0, tzinfo=UTC)
FAILED_AT = NOW - timedelta(hours=2)


@time_machine.travel(NOW, tick=False)
def test_reopens_failed_and_next_run_succeeds() -> None:
    received: list[SampleHappenedV1] = []

    # Handler đã được sửa sau khi delivery hết lượt retry
    @handles("shared.sample-happened", name="shared.fixed_handler")
    def fixed_handler(event: SampleHappenedV1) -> None:
        received.append(event)

    delivery = EventDeliveryFactory.create(
        handler="shared.fixed_handler",
        status=DeliveryStatus.FAILED,
        attempts=6,
        next_attempt_at=FAILED_AT,
        failed_at=FAILED_AT,
        last_error="Boom",
    )

    call_command("retry_failed_events", "--event-id", str(delivery.event_id))
    process_delivery(delivery.event_id, "shared.fixed_handler")

    delivery.refresh_from_db()
    assert delivery.status == DeliveryStatus.COMPLETED
    assert delivery.completed_at == NOW
    assert len(received) == 1


def _failed(**kwargs: object) -> EventDelivery:
    return EventDeliveryFactory.create(
        status=DeliveryStatus.FAILED,
        attempts=6,
        next_attempt_at=FAILED_AT,
        next_dispatch_at=FAILED_AT + timedelta(minutes=3),
        failed_at=FAILED_AT,
        last_error="Boom",
        **kwargs,
    )


@time_machine.travel(NOW, tick=False)
def test_resets_schedule_and_counter_and_sets_retried_at() -> None:
    delivery = _failed(handler="shared.broken")

    with capture_logs() as logs:
        call_command("retry_failed_events", "--handler", "shared.broken")

    delivery.refresh_from_db()
    assert (
        delivery.status,
        delivery.attempts,
        delivery.next_attempt_at,
        delivery.next_dispatch_at,
        delivery.retried_at,
    ) == (DeliveryStatus.PENDING, 0, NOW, NOW, NOW)
    # Dấu vết lần lỗi cũ giữ tới khi lần xử lý sau ghi đè
    assert (delivery.failed_at, delivery.last_error) == (FAILED_AT, "Boom")
    assert [(log["event"], log.get("handler"), log.get("count")) for log in logs] == [
        ("event_delivery_retried", "shared.broken", None),
        ("failed_deliveries_retried", None, 1),
    ]


@time_machine.travel(NOW, tick=False)
def test_does_not_reopen_completed_or_rejected() -> None:
    finished = [
        EventDeliveryFactory.create(status=status, completed_at=FAILED_AT, last_error="Boom")
        for status in (DeliveryStatus.COMPLETED, DeliveryStatus.REJECTED)
    ]

    call_command("retry_failed_events", "--all")

    for delivery in finished:
        before = (delivery.status, delivery.completed_at, delivery.retried_at)
        delivery.refresh_from_db()
        assert (delivery.status, delivery.completed_at, delivery.retried_at) == before


@time_machine.travel(NOW, tick=False)
def test_filters_select_only_matching_pairs() -> None:
    event_row = OutboxEventFactory.create()
    other_type = OutboxEventFactory.create(event_type="shared.other-happened")
    target = _failed(event=event_row, handler="shared.broken")
    untouched = [
        _failed(event=event_row, handler="shared.other_handler"),
        _failed(handler="shared.broken"),
        _failed(event=other_type, handler="shared.broken"),
    ]

    call_command(
        "retry_failed_events",
        "--event-id",
        str(event_row.id),
        "--handler",
        "shared.broken",
        "--type",
        "shared.sample-happened",
    )

    target.refresh_from_db()
    assert target.status == DeliveryStatus.PENDING
    for delivery in untouched:
        delivery.refresh_from_db()
        assert delivery.status == DeliveryStatus.FAILED

    call_command("retry_failed_events", "--type", "shared.other-happened")

    untouched[2].refresh_from_db()
    assert untouched[2].status == DeliveryStatus.PENDING
    assert EventDelivery.objects.filter(status=DeliveryStatus.FAILED).count() == 2


def test_requires_a_filter() -> None:
    delivery = _failed()

    with pytest.raises(CommandError):
        call_command("retry_failed_events")

    delivery.refresh_from_db()
    assert delivery.status == DeliveryStatus.FAILED
