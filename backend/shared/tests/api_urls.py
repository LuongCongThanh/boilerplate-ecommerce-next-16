"""Urlconf chỉ dùng cho test của shared/api."""

from typing import Any

from django.urls import path
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

# Stub của DRF chỉ nhận QuerySet; paginator thật nhận mọi sequence, nên dùng list cho gọn
ITEMS: Any = [{"id": i} for i in range(1, 251)]


class ItemListView(GenericAPIView[Any]):
    """Danh sách giả, phân trang bằng `DEFAULT_PAGINATION_CLASS` như view list thật."""

    permission_classes = (AllowAny,)

    def get(self, request: Request) -> Response:
        paginator = self.paginator
        assert paginator is not None
        page: list[Any] | None = paginator.paginate_queryset(ITEMS, request, view=self)
        return paginator.get_paginated_response(page)


urlpatterns = [path("items", ItemListView.as_view())]
