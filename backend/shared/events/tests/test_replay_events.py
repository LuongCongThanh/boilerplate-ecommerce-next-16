from datetime import UTC, datetime, timedelta

import pytest
import time_machine
from django.core.management import call_command
from django.core.management.base import CommandError

from shared.events import handles, operations
from shared.events.models import DeliveryStatus, EventDelivery, OutboxEvent
from shared.events.tests.conftest import SampleHappenedV1
from shared.testing.factories import EventDeliveryFactory, OutboxEventFactory

pytestmark = pytest.mark.django_db

NOW = datetime(2026, 10, 30, 8, 0, tzinfo=UTC)
SINCE = NOW - timedelta(hours=1)


def _register(*names: str) -> None:
    for name in names:

        @handles("shared.sample-happened", name=name)
        def handler(event: SampleHappenedV1) -> None:
            pass


def _listed_event(**kwargs: object) -> OutboxEvent:
    # Relay đã lập danh sách delivery cho sự kiện này
    fields = {"occurred_at": SINCE + timedelta(minutes=5), "deliveries_created_at": SINCE}
    return OutboxEventFactory.create(**(fields | kwargs))


def _handlers_of(event: OutboxEvent) -> list[str]:
    return sorted(EventDelivery.objects.filter(event=event).values_list("handler", flat=True))


@time_machine.travel(NOW, tick=False)
def test_replay_adds_delivery_for_new_handler() -> None:
    _register("shared.old_handler", "shared.new_handler", "shared.other_new_handler")
    event_row = _listed_event()
    EventDeliveryFactory.create(
        event=event_row,
        handler="shared.old_handler",
        status=DeliveryStatus.COMPLETED,
        completed_at=SINCE,
    )
    before_since = _listed_event(occurred_at=SINCE - timedelta(seconds=1))
    other_type = _listed_event(event_type="shared.other-happened")

    call_command(
        "replay_events",
        "--type",
        "shared.sample-happened",
        "--since",
        SINCE.isoformat(),
        "--handler",
        "shared.new_handler",
    )

    added = EventDelivery.objects.get(event=event_row, handler="shared.new_handler")
    assert (added.status, added.attempts, added.next_attempt_at, added.next_dispatch_at) == (
        DeliveryStatus.PENDING,
        0,
        NOW,
        NOW,
    )
    # Chỉ handler được chọn, chỉ sự kiện đúng loại và từ mốc `since`
    assert _handlers_of(event_row) == ["shared.new_handler", "shared.old_handler"]
    assert _handlers_of(before_since) == []
    assert _handlers_of(other_type) == []


@time_machine.travel(NOW, tick=False)
def test_replay_keeps_existing_deliveries(monkeypatch: pytest.MonkeyPatch) -> None:
    _register("shared.failed_handler", "shared.done_handler", "shared.new_handler")
    # Mỗi lô một sự kiện để kiểm cả việc đi qua nhiều lô
    monkeypatch.setattr(operations, "REPLAY_BATCH", 1)
    event_row = _listed_event()
    failed = EventDeliveryFactory.create(
        event=event_row,
        handler="shared.failed_handler",
        status=DeliveryStatus.FAILED,
        attempts=6,
        next_attempt_at=SINCE,
        failed_at=SINCE,
        last_error="Boom",
    )
    done = EventDeliveryFactory.create(
        event=event_row,
        handler="shared.done_handler",
        status=DeliveryStatus.COMPLETED,
        completed_at=SINCE,
    )
    second_event = _listed_event()

    call_command("replay_events", "--type", "shared.sample-happened", "--since", SINCE.isoformat())

    failed.refresh_from_db()
    done.refresh_from_db()
    assert (failed.status, failed.attempts, failed.failed_at, failed.retried_at) == (
        DeliveryStatus.FAILED,
        6,
        SINCE,
        None,
    )
    assert (done.status, done.completed_at) == (DeliveryStatus.COMPLETED, SINCE)
    all_handlers = ["shared.done_handler", "shared.failed_handler", "shared.new_handler"]
    assert _handlers_of(event_row) == all_handlers
    assert _handlers_of(second_event) == all_handlers


@time_machine.travel(NOW, tick=False)
def test_replay_skips_event_not_yet_listed() -> None:
    _register("shared.new_handler")
    unlisted = _listed_event(deliveries_created_at=None)

    call_command("replay_events", "--type", "shared.sample-happened", "--since", SINCE.isoformat())

    # Relay sẽ lập danh sách cùng marker; replay không làm thay
    unlisted.refresh_from_db()
    assert unlisted.deliveries_created_at is None
    assert _handlers_of(unlisted) == []


def test_replay_unknown_handler_errors() -> None:
    _register("shared.new_handler")
    event_row = _listed_event()
    options = ("--type", "shared.sample-happened", "--since", SINCE.isoformat())

    with pytest.raises(CommandError):
        call_command("replay_events", *options, "--handler", "shared.typo_handler")

    assert _handlers_of(event_row) == []
