# Địa giới hành chính: Tỉnh/thành, Phường/xã, `load_geo` và endpoint

Status: resolved

**PR:** #31

Blocked by: 16

Spec: [spec.md](../../spec.md)

Tách từ ticket [09](../09-shared-core/spec.md).

## Việc cần làm

- `shared/geo/`: model `Province`, `Ward` (mã chính thức làm PK).
- Lệnh `load_geo` nạp dữ liệu từ `vietnam-provinces`, chạy lại an toàn. Thêm target `make load-geo` vào `Makefile`.
- Endpoint `GET store/geo/provinces` và `geo/provinces/{code}/wards`.

## Quyết định

Chốt khi grilling ngày 30/10/2026.

| Chủ đề | Quyết định |
|---|---|
| Tài liệu chi phối | `shared/geo/models.py`, `shared/migrations/0002_*`: 03 §1.1–1.2, ADR 0008 (không kế thừa `BaseModel`). `shared/models.py`: 02 §4 (import model của `geo/`). `load_geo.py`, `Makefile`: 03 §0.7 bước 4, 08 §(bảng lệnh `make load-geo`), 02 §3 (`vietnam-provinces` 2026.9.0). `shared/geo/api.py`, `shared/geo/urls.py`, `config/urls.py`: 04 §4.1, §5.1, §5.6 (`GeoDTO`), 02 §4 (`config/urls.py`). Test: 12 |
| Dependency | `vietnam-provinces>=2026.9.0` trong `pyproject.toml`, cùng kiểu ràng buộc với các package khác; `uv.lock` ghim bản 2026.9.0 |
| Định dạng mã | Mã Cục Thống kê có số 0 đứng đầu: tỉnh 2 chữ số (`01`), phường/xã 5 chữ số (`00004`). Package trả int enum nên `load_geo` đệm khi đọc. Mã này là FK của Địa chỉ, Đơn hàng và ánh xạ GHN sau này |
| Model | `Province(code CharField(10) PK, name CharField(255))`; `Ward(code CharField(10) PK, province FK → Province db_column="province_code" PROTECT related_name="wards", name CharField(255))`. Bảng `shared_province`, `shared_ward` khai báo bằng `Meta.db_table` (02 §9.2); index của FK là index `province_code` của 03. `shared/models.py` import hai model này |
| `load_geo` | Upsert trong một transaction bằng `bulk_create(update_conflicts=True)` của Django theo khoá chính: thêm mã mới, cập nhật tên đổi; với phường/xã cập nhật cả tỉnh (`province_id`) để phường/xã chuyển tỉnh trong nguồn vẫn đúng (thêm khi review). Không xoá mã không còn trong nguồn (03 §0.7 bước 4), chỉ log cảnh báo `geo_stale_codes` kèm số lượng. Log `geo_loaded` với số dòng thêm, sửa, giữ nguyên cho tỉnh và phường/xã. Cấu trúc theo `sync_beat_schedule` |
| `make load-geo` | `uv run python manage.py load_geo`, chạy local như `make migrate`; Compose không tự chạy (08 giữ là bước 4 riêng) |
| Route | `config/urls.py` thêm `api/v1/store/geo/` include `shared/geo/urls.py`; path không có `/` cuối như 04 và `/healthz`. Đây là route `api/v1/store/` đầu tiên; module sau tự thêm include của mình |
| View | `shared/geo/api.py`: `ListAPIView` với `permission_classes = (AllowAny,)`, `pagination_class = None`, throttle mặc định (`anon`). Serializer `GeoOutput` liệt kê đúng `code`, `name` với `max_length` 10/255, component OpenAPI tên `GeoDTO` qua `extend_schema_serializer` (04 §5.1, §5.6; hậu tố `DTO` của class dành cho pydantic, 02 §9.2). Response lỗi trong OpenAPI để ticket [22](../22-openapi-error-responses/spec.md). Truy vấn ở `shared/geo/selectors.py`: `list_provinces()`, `province_exists(*, code)`, `list_wards(*, province_code)` |
| Test | `shared/tests/test_load_geo.py`, `shared/tests/test_api_geo.py`; dữ liệu qua `ProvinceFactory`, `WardFactory` ở `shared/testing/factories.py`. Test của `load_geo` giả lập `vietnam-provinces` bằng monkeypatch (ngoại lệ của 12 §1: package dữ liệu chạy trong process, giả lập để tạo nhánh đổi tên, chuyển tỉnh, mã cũ); số đếm dữ liệu thật lấy từ package, không viết cứng |
| Thứ tự | Theo mã tăng dần, không phụ thuộc collation |
| 404 | Tỉnh không tồn tại → `NotFound` → `ErrorDTO` `NOT_FOUND` qua `exception_handler` của ticket 16. Tỉnh có nhưng chưa có phường/xã → `[]` |

## Acceptance criteria

- [x] `make load-geo` chạy hai lần liên tiếp không lỗi, không trùng dữ liệu.
- [x] Endpoint địa giới trả array không phân trang.
- [x] Mã tỉnh không tồn tại trả 404 dạng `ErrorDTO`.
