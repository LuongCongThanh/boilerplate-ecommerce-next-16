"""Consumer: chạy một handler cho một sự kiện và ghi kết quả lên delivery (07 mục 1.1.1, 1.3).

Delivery bị khoá trong toàn transaction xử lý; handler chạy trong savepoint của cùng transaction,
nên tác động DB của handler và trạng thái `completed`/`rejected` commit cùng nhau. Task giao
trùng chờ khoá rồi thấy delivery đã kết thúc thì bỏ qua.
"""

from datetime import datetime, timedelta
from uuid import UUID

import structlog
from django.db import transaction
from django.utils import timezone

from shared.events.models import EventDelivery
from shared.events.registry import registry
from shared.exceptions import DomainError, RetryLater

logger = structlog.get_logger(__name__)

# Chờ trước mỗi lần thử lại sau lần đầu; hết lịch thì delivery `failed` (07 mục 1.3)
RETRY_DELAYS: tuple[timedelta, ...] = (
    timedelta(seconds=10),
    timedelta(minutes=1),
    timedelta(minutes=5),
    timedelta(minutes=15),
    timedelta(minutes=30),
)

_LAST_ERROR_MAX_LENGTH = 500


def process_delivery(event_id: UUID | str, handler_name: str) -> None:
    """Xử lý delivery `(event_id, handler_name)` nếu còn `pending` và đã tới hạn retry.

    `DatabaseError` ngoài savepoint của handler (kết nối hỏng) không bị bắt: toàn transaction
    rollback, relay giao lại theo `next_dispatch_at` đã lưu.
    """
    # Task Celery truyền chuỗi; chuẩn hoá về UUID đúng kiểu của khoá ngoại
    event_uuid = event_id if isinstance(event_id, UUID) else UUID(event_id)
    with transaction.atomic():
        delivery = (
            EventDelivery.objects.select_for_update(of=("self",))
            .select_related("event")
            .filter(event_id=event_uuid, handler=handler_name)
            .first()
        )
        now = timezone.now()
        if delivery is None:
            # Sự kiện đã bị purge hoặc task mang tham số sai: không còn việc để làm
            logger.warning("event_delivery_missing", event_id=str(event_id), handler=handler_name)
            return
        if delivery.status != EventDelivery.Status.PENDING or delivery.next_attempt_at > now:
            return

        event_row = delivery.event
        log = logger.bind(
            event_id=str(event_row.id), event_type=event_row.event_type, handler=handler_name
        )
        handler = registry.get_handler(handler_name)
        event_class = registry.get_event_class(event_row.event_type, event_row.schema_version)
        if handler is None or event_class is None:
            # Lỗi cấu hình/deploy, không phải lỗi handler: giữ `pending`, không tiêu lượt retry
            log.error("event_handler_missing", schema_version=event_row.schema_version)
            return

        try:
            with transaction.atomic():
                event = event_class.model_validate(
                    {
                        **event_row.payload,
                        "event_id": event_row.id,
                        "occurred_at": event_row.occurred_at,
                    }
                )
                handler.func(event)
        except DomainError as exc:
            _reject(delivery, exc, now)
            log.warning("event_rejected", code=exc.code)
        except RetryLater as exc:
            _schedule_retry(delivery, exc, now, log)
        except Exception as exc:
            # Traceback chỉ đi vào log; `last_error` không mang message (03 mục 1.4)
            log.exception("event_handler_error")
            _schedule_retry(delivery, exc, now, log)
        else:
            delivery.status = EventDelivery.Status.COMPLETED
            delivery.completed_at = now
            delivery.save(update_fields=["status", "completed_at"])


def _reject(delivery: EventDelivery, exc: DomainError, now: datetime) -> None:
    delivery.status = EventDelivery.Status.REJECTED
    delivery.completed_at = now
    delivery.last_error = describe_error(exc)
    delivery.save(update_fields=["status", "completed_at", "last_error"])


def _schedule_retry(
    delivery: EventDelivery,
    exc: Exception,
    now: datetime,
    log: structlog.stdlib.BoundLogger,
) -> None:
    delivery.attempts += 1
    delivery.last_error = describe_error(exc)
    fields = ["attempts", "last_error"]
    if delivery.attempts > len(RETRY_DELAYS):
        delivery.status = EventDelivery.Status.FAILED
        delivery.failed_at = now
        fields += ["status", "failed_at"]
        # Sentry bắt log ERROR để cảnh báo delivery cần người vận hành (07 mục 1.3)
        log.error("event_delivery_failed", attempts=delivery.attempts, error=delivery.last_error)
    else:
        retry_at = now + RETRY_DELAYS[delivery.attempts - 1]
        delivery.next_attempt_at = retry_at
        delivery.next_dispatch_at = retry_at
        fields += ["next_attempt_at", "next_dispatch_at"]
        log.info("event_retry_scheduled", attempts=delivery.attempts, retry_at=retry_at)
    delivery.save(update_fields=fields)


def describe_error(exc: BaseException) -> str:
    """Tên class và `code` nếu có, không kèm message để không lọt PII (03 mục 1.4)."""
    code = getattr(exc, "code", None)
    text = type(exc).__name__ if code is None else f"{type(exc).__name__}({code})"
    return text[:_LAST_ERROR_MAX_LENGTH]
