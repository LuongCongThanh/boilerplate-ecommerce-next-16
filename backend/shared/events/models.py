"""Outbox sự kiện và delivery từng handler (03 mục 1.3, 1.4; ADR 0007).

Không kế thừa `BaseModel`: 03 không có `created_at`/`updated_at` cho hai bảng này. Khoá chính
vẫn là UUID v7 (ADR 0008).
"""

from django.db import models
from django.db.models import Q

from shared.events.registry import HANDLER_NAME_MAX_LENGTH
from shared.models import uuid7


class OutboxEvent(models.Model):
    # Chính là `event_id` trong `DomainEvent`
    id = models.UUIDField(primary_key=True, default=uuid7, editable=False)
    event_type = models.CharField(max_length=100)
    schema_version = models.SmallIntegerField()
    payload = models.JSONField()
    occurred_at = models.DateTimeField()
    # NULL = relay chưa lập danh sách delivery; không có nghĩa handler đã chạy (07 mục 1.1.1)
    deliveries_created_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "shared_outbox_event"
        constraints = (
            models.CheckConstraint(
                condition=Q(schema_version__gte=1),
                name="shared_outbox_event_schema_version_gte_1",
            ),
        )
        indexes = (
            models.Index(
                fields=["occurred_at"],
                condition=Q(deliveries_created_at__isnull=True),
                name="outbox_event_undelivered_idx",
            ),
        )

    def __str__(self) -> str:
        return f"{self.event_type} v{self.schema_version} {self.id}"


class DeliveryStatus(models.TextChoices):
    PENDING = "pending"
    COMPLETED = "completed"
    REJECTED = "rejected"
    FAILED = "failed"


# Delivery đã kết thúc và có `completed_at`
_FINISHED = [DeliveryStatus.COMPLETED, DeliveryStatus.REJECTED]


class EventDelivery(models.Model):
    """Công việc của một handler với một sự kiện, đồng thời là dấu đã xử lý."""

    id = models.UUIDField(primary_key=True, default=uuid7, editable=False)
    # UNIQUE(event_id, handler) đã có index bắt đầu bằng event_id, không cần index riêng của FK
    event = models.ForeignKey(
        OutboxEvent,
        on_delete=models.CASCADE,
        related_name="deliveries",
        db_column="event_id",
        db_index=False,
    )
    handler = models.CharField(max_length=HANDLER_NAME_MAX_LENGTH)
    status = models.CharField(
        max_length=32, choices=DeliveryStatus.choices, default=DeliveryStatus.PENDING
    )
    attempts = models.IntegerField(default=0)
    # Số lần liên tiếp handler đã bắt đầu chạy mà consumer không lưu được kết quả (07 mục 1.3)
    interrupted_runs = models.IntegerField(default=0)
    next_attempt_at = models.DateTimeField()
    next_dispatch_at = models.DateTimeField()
    last_dispatched_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(default="", blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)
    retried_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "shared_event_delivery"
        constraints = (
            models.UniqueConstraint(
                fields=["event", "handler"], name="shared_event_delivery_event_handler_uniq"
            ),
            models.CheckConstraint(
                condition=Q(status__in=DeliveryStatus.values),
                name="shared_event_delivery_status_valid",
            ),
            models.CheckConstraint(
                condition=Q(attempts__gte=0), name="shared_event_delivery_attempts_gte_0"
            ),
            models.CheckConstraint(
                condition=Q(interrupted_runs__gte=0),
                name="shared_event_delivery_interrupted_runs_gte_0",
            ),
            # (status IN ('completed', 'rejected')) = (completed_at IS NOT NULL)
            models.CheckConstraint(
                condition=(
                    Q(status__in=_FINISHED, completed_at__isnull=False)
                    | (~Q(status__in=_FINISHED) & Q(completed_at__isnull=True))
                ),
                name="shared_event_delivery_completed_at_matches_status",
            ),
            models.CheckConstraint(
                condition=~Q(status=DeliveryStatus.FAILED) | Q(failed_at__isnull=False),
                name="shared_event_delivery_failed_has_failed_at",
            ),
        )
        indexes = (
            models.Index(
                fields=["next_dispatch_at", "next_attempt_at"],
                condition=Q(status=DeliveryStatus.PENDING),
                name="event_delivery_pending_idx",
            ),
            models.Index(
                fields=["failed_at"],
                condition=Q(status=DeliveryStatus.FAILED),
                name="event_delivery_failed_idx",
            ),
        )

    def __str__(self) -> str:
        return f"{self.handler} {self.status} {self.event_id}"
