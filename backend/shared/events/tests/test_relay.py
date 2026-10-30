import threading
from datetime import UTC, datetime, timedelta
from unittest import mock

import pytest
import time_machine
from django.core.management import call_command
from django.db import DatabaseError, connection, transaction
from kombu.exceptions import OperationalError
from structlog.testing import capture_logs

from shared.events import handles, publish, relay
from shared.events.models import EventDelivery, OutboxEvent
from shared.events.tasks import dispatch_event
from shared.events.tests.conftest import HandlerEffect, SampleHappenedV1
from shared.testing.factories import EventDeliveryFactory, OutboxEventFactory

pytestmark = pytest.mark.django_db

NOW = datetime(2026, 10, 30, 8, 0, tzinfo=UTC)
ORDER_CODE = "FS2610-7K3QZD"


class Rollback(Exception):
    pass


def _register_recorder(effects: type[HandlerEffect], name: str) -> None:
    @handles("shared.sample-happened", name=name)
    def record(event: SampleHappenedV1) -> None:
        effects.objects.create(handler=name, order_code=event.order_code)


def test_rolled_back_publish_creates_no_delivery() -> None:
    @handles("shared.sample-happened", name="shared.record_call")
    def record_call(event: SampleHappenedV1) -> None:
        pass

    def place_and_fail() -> None:
        with transaction.atomic():
            publish(SampleHappenedV1(order_code=ORDER_CODE, amount=250000))
            raise Rollback

    with pytest.raises(Rollback):
        place_and_fail()

    assert relay.create_deliveries() == 0
    assert not OutboxEvent.objects.exists()
    assert not EventDelivery.objects.exists()


@time_machine.travel(NOW, tick=False)
def test_create_deliveries_one_per_handler_with_marker() -> None:
    @handles("shared.sample-happened", name="shared.first")
    def first(event: SampleHappenedV1) -> None:
        pass

    @handles("shared.sample-happened", name="shared.second")
    def second(event: SampleHappenedV1) -> None:
        pass

    # Handler của bản schema khác không nhận sự kiện v1
    @handles("shared.sample-happened", version=2, name="shared.v2_only")
    def v2_only(event: SampleHappenedV1) -> None:
        pass

    event_row = OutboxEventFactory.create()

    assert relay.create_deliveries() == 1

    event_row.refresh_from_db()
    assert event_row.deliveries_created_at == NOW
    deliveries = EventDelivery.objects.filter(event=event_row).order_by("handler")
    assert [
        (d.handler, d.status, d.attempts, d.next_attempt_at, d.next_dispatch_at) for d in deliveries
    ] == [
        ("shared.first", EventDelivery.Status.PENDING, 0, NOW, NOW),
        ("shared.second", EventDelivery.Status.PENDING, 0, NOW, NOW),
    ]
    # Sự kiện đã có marker không bị lập danh sách lại
    assert relay.create_deliveries() == 0
    assert EventDelivery.objects.count() == 2


@time_machine.travel(NOW, tick=False)
def test_event_without_handlers_gets_marker() -> None:
    event_row = OutboxEventFactory.create()

    with capture_logs() as logs:
        assert relay.create_deliveries() == 1

    event_row.refresh_from_db()
    assert event_row.deliveries_created_at == NOW
    assert not EventDelivery.objects.exists()
    assert {
        "event": "outbox_event_no_handlers",
        "event_id": str(event_row.id),
        "event_type": "shared.sample-happened",
        "schema_version": 1,
    }.items() <= logs[0].items()


@pytest.mark.django_db(transaction=True)
def test_two_relays_concurrently_create_no_duplicates() -> None:
    for name in ("shared.first", "shared.second"):
        handles("shared.sample-happened", name=name)(lambda event: None)
    events = OutboxEventFactory.create_batch(30)
    barrier = threading.Barrier(2)
    errors: list[BaseException] = []

    def run() -> None:
        try:
            barrier.wait()
            # Batch nhỏ để hai relay cùng quét nhiều vòng trên cùng tập sự kiện
            while relay.create_deliveries(batch=5):
                pass
        except BaseException as exc:
            errors.append(exc)
        finally:
            connection.close()

    threads = [threading.Thread(target=run) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert errors == []
    assert not OutboxEvent.objects.filter(deliveries_created_at__isnull=True).exists()
    assert EventDelivery.objects.count() == len(events) * 2
    pairs = set(EventDelivery.objects.values_list("event_id", "handler"))
    assert pairs == {
        (event.id, name) for event in events for name in ("shared.first", "shared.second")
    }


def test_lost_task_redispatched_after_deadline(
    handler_effect_table: type[HandlerEffect],
) -> None:
    _register_recorder(handler_effect_table, "shared.record_effect")
    with time_machine.travel(NOW, tick=False) as traveller:
        publish(SampleHappenedV1(order_code=ORDER_CODE, amount=250000))
        relay.create_deliveries()

        # Broker nhận task rồi mất: lần giao đầu không tới worker
        with mock.patch.object(dispatch_event, "apply_async") as lost:
            assert relay.dispatch_due() == 1
            lost.assert_called_once()
            delivery = EventDelivery.objects.get()
            assert delivery.next_dispatch_at == NOW + relay.REDISPATCH_AFTER
            assert delivery.last_dispatched_at == NOW
            assert delivery.status == EventDelivery.Status.PENDING

            # Chưa tới hạn giao lại thì relay không giao trùng
            traveller.shift(timedelta(minutes=2))
            assert relay.dispatch_due() == 0
            lost.assert_called_once()

        traveller.shift(timedelta(minutes=1, seconds=1))
        assert relay.dispatch_due() == 1

    delivery.refresh_from_db()
    assert delivery.status == EventDelivery.Status.COMPLETED
    # Task mất không tiêu lượt retry
    assert delivery.attempts == 0
    assert handler_effect_table.objects.count() == 1


@time_machine.travel(NOW, tick=False)
def test_broker_error_keeps_delivery_for_later() -> None:
    delivery = EventDeliveryFactory.create(handler="shared.record_call")

    with (
        mock.patch.object(
            dispatch_event, "apply_async", side_effect=OperationalError("broker down")
        ),
        capture_logs() as logs,
    ):
        assert relay.dispatch_due() == 1

    delivery.refresh_from_db()
    assert delivery.status == EventDelivery.Status.PENDING
    assert delivery.attempts == 0
    assert delivery.last_error == ""
    # Hạn giao lại đã commit trước khi gọi broker: relay thử lại sau hạn
    assert delivery.next_dispatch_at == NOW + relay.REDISPATCH_AFTER
    failed = [log for log in logs if log["event"] == "outbox_dispatch_failed"]
    assert failed[0]["log_level"] == "error"
    assert failed[0]["handler"] == "shared.record_call"
    assert failed[0]["event_id"] == str(delivery.event_id)


@time_machine.travel(NOW, tick=False)
def test_dispatch_skips_retry_not_due() -> None:
    later = NOW + timedelta(seconds=10)
    due = EventDeliveryFactory.create()
    EventDeliveryFactory.create(attempts=1, next_attempt_at=later, next_dispatch_at=NOW)
    EventDeliveryFactory.create(next_attempt_at=NOW, next_dispatch_at=later)
    EventDeliveryFactory.create(status=EventDelivery.Status.COMPLETED, completed_at=NOW)
    EventDeliveryFactory.create(status=EventDelivery.Status.FAILED, failed_at=NOW, attempts=6)

    with mock.patch.object(dispatch_event, "apply_async") as apply_async:
        assert relay.dispatch_due() == 1

    apply_async.assert_called_once_with(args=(str(due.event_id), due.handler), queue="events")


@time_machine.travel(NOW, tick=False)
def test_run_outbox_relay_once(handler_effect_table: type[HandlerEffect]) -> None:
    _register_recorder(handler_effect_table, "shared.first")
    _register_recorder(handler_effect_table, "shared.second")
    publish(SampleHappenedV1(order_code=ORDER_CODE, amount=250000))

    call_command("run_outbox_relay", "--once")

    assert set(EventDelivery.objects.values_list("handler", "status")) == {
        ("shared.first", EventDelivery.Status.COMPLETED),
        ("shared.second", EventDelivery.Status.COMPLETED),
    }
    assert sorted(handler_effect_table.objects.values_list("handler", flat=True)) == [
        "shared.first",
        "shared.second",
    ]


@pytest.mark.django_db(transaction=True)
def test_run_outbox_relay_survives_iteration_error() -> None:
    # transaction=True: kết nối ở autocommit như tiến trình relay thật, nên việc dọn kết nối
    # sau lỗi không đóng transaction của test
    with (
        mock.patch.object(relay, "create_deliveries", side_effect=DatabaseError("db down")),
        capture_logs() as logs,
    ):
        call_command("run_outbox_relay", "--once")

    failed = [log for log in logs if log["event"] == "outbox_relay_iteration_failed"]
    assert failed[0]["log_level"] == "error"
