"""Celery app, queue và lịch job (nguồn chuẩn cho `sync_beat_schedule`, 07 mục 3.2)."""

import os

from celery import Celery
from kombu import Queue

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

app = Celery("config")
app.config_from_object("django.conf:settings", namespace="CELERY")

# Local chạy một worker cho cả 4 queue (07 mục 3.1)
app.conf.task_queues = [Queue(name) for name in ("default", "events", "emails", "integrations")]

# Lịch job thêm ở ticket tạo ra job đó
app.conf.beat_schedule = {}

# Mặc định Celery chỉ tìm <app>.tasks, nên liệt kê từng package có tasks.py (02 mục 5)
app.autodiscover_tasks(["shared"])
