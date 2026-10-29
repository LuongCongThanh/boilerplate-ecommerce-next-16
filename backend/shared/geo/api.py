"""GET /api/v1/store/geo/provinces và /geo/provinces/{code}/wards (04 mục 4.1).

Công khai, trả array `GeoDTO` không phân trang (04 mục 5.1).
"""

from typing import Any

from django.db.models import QuerySet
from rest_framework import serializers
from rest_framework.exceptions import NotFound
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny

from shared.geo import selectors
from shared.geo.models import Province, Ward


class GeoOutput(serializers.Serializer[Any]):
    code = serializers.CharField()
    name = serializers.CharField()


class ProvinceListView(ListAPIView[Province]):
    permission_classes = (AllowAny,)
    pagination_class = None
    serializer_class = GeoOutput

    def get_queryset(self) -> QuerySet[Province]:
        return selectors.list_provinces()


class WardListView(ListAPIView[Ward]):
    permission_classes = (AllowAny,)
    pagination_class = None
    serializer_class = GeoOutput

    def get_queryset(self) -> QuerySet[Ward]:
        code = self.kwargs["code"]
        # Tỉnh có nhưng chưa có phường/xã vẫn trả []; chỉ mã tỉnh lạ mới là 404
        if selectors.find_province(code=code) is None:
            raise NotFound
        return selectors.list_wards(province_code=code)
