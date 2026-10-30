"""Celery task giao một delivery cho consumer (07 mục 1.1.1, 3.1)."""

from celery import shared_task

from shared.events.consumer import process_delivery


@shared_task(name="shared.dispatch_event", queue="events")
def dispatch_event(event_id: str, handler_name: str) -> None:
    # Trạng thái và lịch retry nằm trên delivery trong PostgreSQL, không dùng retry của Celery
    process_delivery(event_id, handler_name)
