from datetime import UTC, datetime

import pytest
import structlog
import time_machine
from django.core.exceptions import ImproperlyConfigured
from django.db import transaction

from shared.events import DomainEvent, handles, publish
from shared.events.models import OutboxEvent
from shared.events.registry import registry
from shared.events.tests.conftest import SampleHappenedV1

pytestmark = pytest.mark.django_db


class Boom(Exception):
    pass


@time_machine.travel(datetime(2026, 10, 30, 8, 0, tzinfo=UTC), tick=False)
def test_publish_writes_outbox_row_in_current_transaction() -> None:
    with structlog.contextvars.bound_contextvars(request_id="req-1"):
        event = SampleHappenedV1(order_code="FS2610-7K3QZD", amount=250000)

    with transaction.atomic():
        publish(event)
        row = OutboxEvent.objects.get()

    assert row.id == event.event_id
    assert row.id.version == 7
    assert row.event_type == "shared.sample-happened"
    assert row.schema_version == 1
    assert row.occurred_at == datetime(2026, 10, 30, 8, 0, tzinfo=UTC)
    assert row.payload == {
        "order_code": "FS2610-7K3QZD",
        "amount": 250000,
        "correlation_id": "req-1",
    }
    assert row.deliveries_created_at is None


def _publish_then_fail() -> None:
    with transaction.atomic():
        publish(SampleHappenedV1(order_code="FS2610-7K3QZD", amount=1))
        raise Boom


def test_publish_rolled_back_with_transaction() -> None:
    with pytest.raises(Boom):
        _publish_then_fail()

    assert not OutboxEvent.objects.exists()


def test_handles_rejects_duplicate_name() -> None:
    @handles("shared.sample-happened", name="shared.record_sample")
    def first(event: SampleHappenedV1) -> None: ...

    with pytest.raises(ImproperlyConfigured, match=r"shared\.record_sample"):

        @handles("shared.sample-happened", version=1, name="shared.record_sample")
        def second(event: SampleHappenedV1) -> None: ...

    registered = registry.get_handler("shared.record_sample")
    assert registered is not None
    assert registered.func is first
    assert [h.name for h in registry.handlers_for("shared.sample-happened", 1)] == [
        "shared.record_sample"
    ]


def test_duplicate_event_class_rejected() -> None:
    assert registry.get_event_class("shared.sample-happened", 1) is SampleHappenedV1

    with pytest.raises(ImproperlyConfigured, match=r"shared\.sample-happened"):

        class OtherSampleV1(DomainEvent):
            event_type = "shared.sample-happened"
            schema_version = 1

    assert registry.get_event_class("shared.sample-happened", 1) is SampleHappenedV1
