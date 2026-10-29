"""Phân trang chuẩn cho API: `page_size` mặc định 24, tối đa 100 (04 mục 5.1)."""

from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.request import Request


class StandardPagination(PageNumberPagination):
    page_size = 24
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_page_size(self, request: Request) -> int:
        raw = request.query_params.get(self.page_size_query_param)
        if raw is None:
            return self.page_size
        try:
            value = int(raw)
        except ValueError:
            raise ValidationError({"page_size": ["Phải là số nguyên."]}) from None
        if value < 1:
            raise ValidationError({"page_size": ["Phải lớn hơn hoặc bằng 1."]})
        return min(value, self.max_page_size)
