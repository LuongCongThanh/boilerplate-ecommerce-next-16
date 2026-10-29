"""Tra cứu tỉnh/thành, phường/xã."""

from django.db.models import QuerySet

from shared.geo.models import Province, Ward

# Mã là chuỗi số cùng độ dài nên thứ tự chuỗi trùng thứ tự số, không phụ thuộc collation


def list_provinces() -> QuerySet[Province]:
    return Province.objects.order_by("code")


def find_province(*, code: str) -> Province | None:
    return Province.objects.filter(code=code).first()


def list_wards(*, province_code: str) -> QuerySet[Ward]:
    return Ward.objects.filter(province_id=province_code).order_by("code")
