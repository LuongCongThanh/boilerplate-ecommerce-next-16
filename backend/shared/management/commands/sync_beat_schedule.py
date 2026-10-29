"""Đồng bộ lịch job từ `config/celery.py` vào `django-celery-beat` (07 mục 3.2).

Code là nguồn chuẩn: tên `PeriodicTask` là key của `beat_schedule`; `task`, lịch, `queue`,
`enabled` được ghi theo code. Job có trong DB mà không còn trong code bị tắt, không bị xoá.
Chỉ hỗ trợ lịch crontab và interval. Mỗi thay đổi ghi một dòng log; chạy lại không đổi gì.
"""

from datetime import timedelta
from typing import Any

import structlog
from celery.schedules import crontab, schedule
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django_celery_beat.models import CrontabSchedule, IntervalSchedule, PeriodicTask

from config.celery import app

logger = structlog.get_logger(__name__)


class Command(BaseCommand):
    help = "Đồng bộ lịch job Celery Beat từ config/celery.py vào database."

    @transaction.atomic
    def handle(self, *args: object, **options: object) -> None:
        beat_schedule: dict[str, dict[str, Any]] = app.conf.beat_schedule
        for name, entry in beat_schedule.items():
            _sync_job(name, entry)
        for task in PeriodicTask.objects.filter(enabled=True).exclude(name__in=list(beat_schedule)):
            task.enabled = False
            task.save()
            logger.info("beat_job_disabled", name=task.name)


def _sync_job(name: str, entry: dict[str, Any]) -> None:
    interval, cron = _resolve_schedule_row(name, entry["schedule"])
    wanted = {
        "task": entry["task"],
        "interval": interval,
        "crontab": cron,
        # PeriodicTask chỉ nhận một loại lịch: bỏ solar, clocked nếu job trong DB đang dùng
        "solar": None,
        "clocked": None,
        "queue": entry.get("options", {}).get("queue"),
        "enabled": True,
    }
    task = PeriodicTask.objects.filter(name=name).first()
    if task is None:
        PeriodicTask(name=name, **wanted).save()
        logger.info("beat_job_created", name=name)
        return
    changed = [field for field, value in wanted.items() if getattr(task, field) != value]
    if changed:
        for field in changed:
            setattr(task, field, wanted[field])
        task.save()
        logger.info("beat_job_updated", name=name, fields=changed)


def _resolve_schedule_row(
    name: str, job_schedule: object
) -> tuple[IntervalSchedule | None, CrontabSchedule | None]:
    """Dòng lịch khớp với lịch trong code, tạo mới khi chưa có."""
    if isinstance(job_schedule, crontab):
        cron = CrontabSchedule.from_schedule(job_schedule)
        if cron.pk is None:
            cron.save()
        return None, cron
    if isinstance(job_schedule, int | float | timedelta):
        job_schedule = schedule(job_schedule)
    if isinstance(job_schedule, schedule):
        spec = {
            "every": int(job_schedule.run_every.total_seconds()),
            "period": IntervalSchedule.SECONDS,
        }
        interval = IntervalSchedule.objects.filter(**spec).order_by("pk").first()
        return interval or IntervalSchedule.objects.create(**spec), None
    raise CommandError(f"{name}: chỉ hỗ trợ lịch crontab và interval, nhận {job_schedule!r}")
