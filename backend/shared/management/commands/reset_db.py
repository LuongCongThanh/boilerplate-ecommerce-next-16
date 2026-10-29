"""Xoá và tạo lại database của máy dev cho `make db-reset` (08 mục 3).

Nối database `postgres` bằng chính role của `DATABASES["default"]`, `DROP DATABASE … WITH
(FORCE)` rồi `CREATE DATABASE … OWNER <role>`; role giữ nguyên. Chỉ chạy khi `DEBUG` bật và
host là `localhost`/`127.0.0.1`, để không bao giờ xoá database của staging hoặc production.
Migrate và `sync_beat_schedule` do recipe của Makefile gọi sau lệnh này.
"""

import psycopg
import structlog
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connections
from psycopg import sql

logger = structlog.get_logger(__name__)

LOCAL_HOSTS = frozenset({"localhost", "127.0.0.1"})


class Command(BaseCommand):
    help = "Xoá và tạo lại database của máy dev (chỉ khi DEBUG bật và host là localhost)."

    def handle(self, *args: object, **options: object) -> None:
        if not settings.DEBUG:
            raise CommandError("reset_db chỉ chạy khi DEBUG bật (máy dev)")
        db = settings.DATABASES["default"]
        if db["HOST"] not in LOCAL_HOSTS:
            raise CommandError(
                f"reset_db chỉ chạy với database trên máy (localhost, 127.0.0.1), "
                f"host đang là {db['HOST']!r}"
            )

        name, owner = db["NAME"], db["USER"]
        # Đóng kết nối Django đang giữ tới database sắp xoá
        connections.close_all()
        with psycopg.connect(
            dbname="postgres",
            host=db["HOST"],
            port=db["PORT"],
            user=owner,
            password=db["PASSWORD"],
            autocommit=True,  # DROP/CREATE DATABASE không chạy được trong transaction
        ) as conn:
            conn.execute(
                sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(sql.Identifier(name))
            )
            conn.execute(
                sql.SQL("CREATE DATABASE {} OWNER {}").format(
                    sql.Identifier(name), sql.Identifier(owner)
                )
            )
        logger.info("database_reset", name=name)
