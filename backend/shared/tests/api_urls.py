"""Urlconf chỉ dùng cho test của shared/api."""

from typing import Any

from django.urls import path
from rest_framework import serializers
from rest_framework.exceptions import Throttled
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from shared.api.throttling import AnonThrottle
from shared.exceptions import DomainError

# Stub của DRF chỉ nhận QuerySet; paginator thật nhận mọi sequence, nên dùng list cho gọn
ITEMS: Any = [{"id": i} for i in range(1, 251)]

# Urlconf ghi đè ROOT_URLCONF nên phải khai báo lại handler như config/urls.py
handler404 = "shared.api.views.not_found"
handler500 = "shared.api.views.server_error"


class ItemListView(GenericAPIView[Any]):
    """Danh sách giả, phân trang bằng `DEFAULT_PAGINATION_CLASS` như view list thật."""

    permission_classes = (AllowAny,)

    def get(self, request: Request) -> Response:
        paginator = self.paginator
        assert paginator is not None
        page: list[Any] | None = paginator.paginate_queryset(ITEMS, request, view=self)
        return paginator.get_paginated_response(page)


class AddressSerializer(serializers.Serializer[Any]):
    city = serializers.CharField()


class LineSerializer(serializers.Serializer[Any]):
    sku = serializers.CharField()


class ProfileSerializer(serializers.Serializer[Any]):
    name = serializers.CharField()
    address = AddressSerializer()
    lines = LineSerializer(many=True, required=False)


class ValidateView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request: Request) -> Response:
        serializer = ProfileSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data)


class OutOfStock(DomainError):
    code = "OUT_OF_STOCK"
    http_status = 409
    message = "Một số sản phẩm không đủ hàng."


class DomainErrorView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request: Request) -> Response:
        raise OutOfStock(details={"items": [{"sku": "A", "requested": 3, "available": 1}]})


class ThrottledView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request: Request) -> Response:
        raise Throttled(wait=30)


class BoomView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request: Request) -> Response:
        raise RuntimeError("secret internal detail")


class DefaultPermissionView(APIView):
    """Không khai báo `permission_classes`: dùng `DEFAULT_PERMISSION_CLASSES`."""

    def get(self, request: Request) -> Response:
        return Response({})


class ThrottleKeyView(APIView):
    """Trả khoá mà `AnonThrottle` dùng cho request này, để test IP mà throttle thấy."""

    permission_classes = (AllowAny,)
    throttle_classes = ()

    def get(self, request: Request) -> Response:
        return Response({"key": AnonThrottle().get_cache_key(request, self)})


urlpatterns = [
    path("items", ItemListView.as_view()),
    path("validate", ValidateView.as_view()),
    path("domain-error", DomainErrorView.as_view()),
    path("throttled", ThrottledView.as_view()),
    path("boom", BoomView.as_view()),
    path("private", DefaultPermissionView.as_view()),
    path("throttle-key", ThrottleKeyView.as_view()),
]
