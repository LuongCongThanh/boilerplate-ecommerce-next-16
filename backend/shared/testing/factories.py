"""Factory gốc dùng chung cho test (02 mục 5, mục 9.5)."""

import factory
from django.utils import timezone
from factory.django import DjangoModelFactory

from shared.events.models import EventDelivery, OutboxEvent
from shared.geo.models import Province, Ward


class ProvinceFactory(DjangoModelFactory[Province]):
    class Meta:
        model = Province

    code = factory.Sequence(lambda n: f"{n:02d}")
    name = factory.Sequence(lambda n: f"Tỉnh {n}")


class WardFactory(DjangoModelFactory[Ward]):
    class Meta:
        model = Ward

    code = factory.Sequence(lambda n: f"{n:05d}")
    province = factory.SubFactory(ProvinceFactory)
    name = factory.Sequence(lambda n: f"Phường {n}")


class OutboxEventFactory(DjangoModelFactory[OutboxEvent]):
    """Dòng outbox chưa lập danh sách delivery.

    Mặc định khớp sự kiện mẫu `shared.sample-happened` v1 trong test của `shared.events`; module
    khác truyền `event_type`, `schema_version`, `payload` của sự kiện thật.
    """

    class Meta:
        model = OutboxEvent

    event_type = "shared.sample-happened"
    schema_version = 1
    payload = factory.LazyFunction(lambda: {"order_code": "FS2610-7K3QZD", "amount": 250000})
    occurred_at = factory.LazyFunction(timezone.now)


class EventDeliveryFactory(DjangoModelFactory[EventDelivery]):
    """Delivery `pending` tới hạn cả retry lẫn giao lại."""

    class Meta:
        model = EventDelivery

    event = factory.SubFactory(OutboxEventFactory)
    handler = factory.Sequence(lambda n: f"shared.handler_{n}")
    next_attempt_at = factory.LazyFunction(timezone.now)
    next_dispatch_at = factory.LazyAttribute(lambda delivery: delivery.next_attempt_at)
