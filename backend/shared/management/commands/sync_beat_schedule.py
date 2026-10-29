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
        code_schedule: dict[str, dict[str, Any]] = app.conf.beat_schedule
        for name, entry in code_schedule.items():
            _sync_job(name, entry)
        for task in PeriodicTask.objects.filter(enabled=True).exclude(name__in=list(code_schedule)):
            task.enabled = False
            task.save()
            logger.info("beat_job_disabled", name=task.name)


def _sync_job(name: str, entry: dict[str, Any]) -> None:
    interval, cron = _schedule_rows(name, entry["schedule"])
    wanted = {
        "task": entry["task"],
        "interval": interval,
        "crontab": cron,
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


def _schedule_rows(
    name: str, code_schedule: object
) -> tuple[IntervalSchedule | None, CrontabSchedule | None]:
    """Dòng lịch khớp với lịch trong code, tạo mới khi chưa có."""
    if isinstance(code_schedule, crontab):
        cron = CrontabSchedule.from_schedule(code_schedule)
        if cron.pk is None:
            cron.save()
        return None, cron
    if isinstance(code_schedule, int | float | timedelta):
        code_schedule = schedule(code_schedule)
    if isinstance(code_schedule, schedule):
        spec = {
            "every": int(code_schedule.run_every.total_seconds()),
            "period": IntervalSchedule.SECONDS,
        }
        interval = IntervalSchedule.objects.filter(**spec).order_by("pk").first()
        return interval or IntervalSchedule.objects.create(**spec), None
    raise CommandError(f"{name}: chỉ hỗ trợ lịch crontab và interval, nhận {code_schedule!r}")
