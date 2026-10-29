from types import SimpleNamespace

import pytest
from django.core.management import call_command
from structlog.testing import capture_logs
from vietnam_provinces import Province as SourceProvince
from vietnam_provinces import Ward as SourceWard

from shared.models import Province, Ward

pytestmark = pytest.mark.django_db


def test_load_geo_twice_creates_no_duplicates() -> None:
    call_command("load_geo")

    with capture_logs() as logs:
        call_command("load_geo")

    assert Province.objects.count() == 34
    assert Ward.objects.count() == 3321
    loaded = [log for log in logs if log["event"] == "geo_loaded"]
    assert len(loaded) == 1
    assert loaded[0]["provinces"] == {"created": 0, "updated": 0, "unchanged": 34}
    assert loaded[0]["wards"] == {"created": 0, "updated": 0, "unchanged": 3321}


def test_codes_are_zero_padded() -> None:
    call_command("load_geo")

    assert Province.objects.get(code="01").name == "Thành phố Hà Nội"
    ba_dinh = Ward.objects.get(code="00004")
    assert ba_dinh.name == "Phường Ba Đình"
    assert ba_dinh.province_id == "01"
    assert {len(code) for code in Province.objects.values_list("code", flat=True)} == {2}
    assert {len(code) for code in Ward.objects.values_list("code", flat=True)} == {5}


def test_rerun_updates_renamed_and_keeps_missing_codes(monkeypatch: pytest.MonkeyPatch) -> None:
    # Nguồn giả: package trả mã dạng int như ProvinceCode, WardCode
    source_provinces = [
        SimpleNamespace(code=1, name="Tỉnh Giả Đổi Tên"),
        SimpleNamespace(code=2, name="Tỉnh Giả Mới"),
    ]
    source_wards = [
        SimpleNamespace(code=4, province_code=1, name="Xã Giả Giữ Nguyên"),
        SimpleNamespace(code=10, province_code=2, name="Xã Giả Mới"),
    ]
    monkeypatch.setattr(SourceProvince, "iter_all", lambda: iter(source_provinces))
    monkeypatch.setattr(SourceWard, "iter_all", lambda: iter(source_wards))
    Province.objects.create(code="01", name="Tỉnh Giả Tên Cũ")
    Province.objects.create(code="99", name="Tỉnh Giả Đã Bỏ")
    Ward.objects.create(code="00004", province_id="01", name="Xã Giả Giữ Nguyên")
    Ward.objects.create(code="99999", province_id="99", name="Xã Giả Đã Bỏ")

    with capture_logs() as logs:
        call_command("load_geo")

    assert dict(Province.objects.values_list("code", "name")) == {
        "01": "Tỉnh Giả Đổi Tên",
        "02": "Tỉnh Giả Mới",
        "99": "Tỉnh Giả Đã Bỏ",
    }
    assert sorted(Ward.objects.values_list("code", "province_id", "name")) == [
        ("00004", "01", "Xã Giả Giữ Nguyên"),
        ("00010", "02", "Xã Giả Mới"),
        ("99999", "99", "Xã Giả Đã Bỏ"),
    ]
    stale = [log for log in logs if log["event"] == "geo_stale_codes"]
    assert len(stale) == 1
    assert stale[0]["log_level"] == "warning"
    assert (stale[0]["provinces"], stale[0]["wards"]) == (1, 1)
    loaded = [log for log in logs if log["event"] == "geo_loaded"]
    assert len(loaded) == 1
    assert loaded[0]["provinces"] == {"created": 1, "updated": 1, "unchanged": 0}
    assert loaded[0]["wards"] == {"created": 1, "updated": 0, "unchanged": 1}
