"""Model cơ sở cho các bảng do dự án định nghĩa (03 mục 0.1, ADR 0008)."""

import uuid
from typing import Any

from django.db import models
from django.utils import timezone


def uuid7() -> uuid.UUID:
    # Migration ghi đường dẫn hàm này, không ghi `uuid.uuid7`: đổi cách sinh UUID chỉ cần sửa
    # thân hàm (ADR 0008)
    return uuid.uuid7()


class BaseQuerySet[M: models.Model](models.QuerySet[M]):
    """Giữ `updated_at` đúng cho các đường ghi bulk, nơi `auto_now` không chạy."""

    def update(self, **kwargs: Any) -> int:
        kwargs.setdefault("updated_at", timezone.now())
        return super().update(**kwargs)

    def bulk_update(self, objs: Any, fields: Any, batch_size: int | None = None) -> int:
        # Không tự gán thay bên gọi: mỗi object có thể đã mang `updated_at` riêng
        if "updated_at" not in fields:
            raise ValueError("bulk_update phải có 'updated_at' trong fields (03 mục 0.1)")
        return super().bulk_update(objs, fields, batch_size=batch_size)


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid7, editable=False)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    objects = BaseQuerySet.as_manager()

    class Meta:
        abstract = True
