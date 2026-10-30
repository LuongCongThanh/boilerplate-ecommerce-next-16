"""Thao tác vận hành outbox cho người vận hành và job theo lịch (07 mục 1.1.1, 1.3).

Management command và Celery task chỉ là lớp mỏng gọi vào các hàm ở đây.
"""

from uuid import UUID

import structlog
from django.db import transaction
from django.utils import timezone

from shared.events.models import DeliveryStatus, EventDelivery

logger = structlog.get_logger(__name__)


def retry_failed_deliveries(
    *,
    event_id: UUID | None = None,
    handler: str | None = None,
    event_type: str | None = None,
) -> int:
    """Mở lại delivery `failed` khớp mọi bộ lọc được truyền; relay sẽ giao lại.

    Đặt `pending`, `attempts = 0`, lịch retry và giao lại về hiện tại, ghi `retried_at`. Giữ
    `failed_at`, `last_error` làm dấu vết tới lần lỗi sau. Delivery `completed`/`rejected` không
    bao giờ được mở lại. Không truyền bộ lọc nào nghĩa là mọi delivery `failed`. Trả số delivery
    đã mở lại.
    """
    deliveries = EventDelivery.objects.filter(status=DeliveryStatus.FAILED)
    if event_id is not None:
        deliveries = deliveries.filter(event_id=event_id)
    if handler is not None:
        deliveries = deliveries.filter(handler=handler)
    if event_type is not None:
        deliveries = deliveries.filter(event__event_type=event_type)

    with transaction.atomic():
        # Khoá rồi lọc lại `failed`: dòng vừa được mở lại ở nơi khác không bị đặt lại lần nữa
        reopened = list(
            deliveries.select_for_update(of=("self",)).values_list("id", "event_id", "handler")
        )
        now = timezone.now()
        EventDelivery.objects.filter(id__in=[delivery_id for delivery_id, _, _ in reopened]).update(
            status=DeliveryStatus.PENDING,
            attempts=0,
            next_attempt_at=now,
            next_dispatch_at=now,
            retried_at=now,
        )
    for _, reopened_event_id, reopened_handler in reopened:
        logger.info(
            "event_delivery_retried", event_id=str(reopened_event_id), handler=reopened_handler
        )
    logger.info("failed_deliveries_retried", count=len(reopened))
    return len(reopened)
