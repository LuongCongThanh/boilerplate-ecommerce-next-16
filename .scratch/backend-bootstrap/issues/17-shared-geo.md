# Địa giới hành chính: Tỉnh/thành, Phường/xã, `load_geo` và endpoint

Status: resolved

**PR:** #31

Blocked by: 16

Spec: [spec.md](../spec.md)

Tách từ ticket [09](./09-shared-core.md).

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
| View | `shared/geo/api.py`: `ListAPIView` với `permission_classes = (AllowAny,)`, `pagination_class = None`, throttle mặc định (`anon`). Serializer `GeoOutput` liệt kê đúng `code`, `name` với `max_length` 10/255, component OpenAPI tên `GeoDTO` qua `extend_schema_serializer` (04 §5.1, §5.6; hậu tố `DTO` của class dành cho pydantic, 02 §9.2). Response lỗi trong OpenAPI để ticket [22](./22-openapi-error-responses.md). Truy vấn ở `shared/geo/selectors.py`: `list_provinces()`, `province_exists(*, code)`, `list_wards(*, province_code)` |
| Test | `shared/tests/test_load_geo.py`, `shared/tests/test_api_geo.py`; dữ liệu qua `ProvinceFactory`, `WardFactory` ở `shared/testing/factories.py`. Test của `load_geo` giả lập `vietnam-provinces` bằng monkeypatch (ngoại lệ của 12 §1: package dữ liệu chạy trong process, giả lập để tạo nhánh đổi tên, chuyển tỉnh, mã cũ); số đếm dữ liệu thật lấy từ package, không viết cứng |
| Thứ tự | Theo mã tăng dần, không phụ thuộc collation |
| 404 | Tỉnh không tồn tại → `NotFound` → `ErrorDTO` `NOT_FOUND` qua `exception_handler` của ticket 16. Tỉnh có nhưng chưa có phường/xã → `[]` |

## Acceptance criteria

- [x] `make load-geo` chạy hai lần liên tiếp không lỗi, không trùng dữ liệu.
- [x] Endpoint địa giới trả array không phân trang.
- [x] Mã tỉnh không tồn tại trả 404 dạng `ErrorDTO`.

## Comments

### Báo cáo 30/10/2026

**Nhánh:** `feat/geo-administrative-units` · **PR:** #31 · **Mode:** full

#### Đã làm

| AC | Bằng chứng |
| --- | --- |
| 1. `make load-geo` chạy hai lần không lỗi, không trùng | `shared/tests/test_load_geo.py::test_load_geo_twice_creates_no_duplicates`, `::test_codes_are_zero_padded`, `::test_rerun_updates_renamed_and_keeps_missing_codes`, `::test_rerun_moves_ward_to_new_province`. Kiểm tay trên DB local: lần 1 tạo 34 tỉnh/thành, 3321 phường/xã; lần 2 `unchanged` 34/3321; DB còn đúng 34/3321, mã đầu `01`/`00004`. Chạy lệnh của recipe (`uv run python manage.py load_geo`) vì máy không có `make` trong PATH |
| 2. Endpoint trả array không phân trang | `shared/tests/test_api_geo.py::test_provinces_returns_unpaginated_array_ordered_by_code`, `::test_wards_of_province_returns_unpaginated_array`, `::test_geo_endpoints_are_public` |
| 3. Mã tỉnh không tồn tại trả 404 `ErrorDTO` | `shared/tests/test_api_geo.py::test_wards_of_unknown_province_returns_404_error_dto` |

Lint xanh (ruff check, ruff format, mypy, lint-imports) · test: 163 passed trong 6.69s. Chạy lệnh tương đương recipe của `make lint` / `make test` vì không có `make` trong PATH.

#### Chưa làm

- Không

#### Gap

- `lint-imports` trên Windows lỗi `UnicodeEncodeError` (cp1252) khi in tên contract tiếng Việt, chạy với `PYTHONUTF8=1` thì xanh. Có từ trước ticket này.
- Mã đã mất khỏi nguồn vẫn được giữ và vẫn hiện ở endpoint (hệ quả của quyết định upsert không xoá). Nếu đợt sắp xếp địa giới sau xoá phường/xã, cần cách ẩn mã cũ.
- Endpoint mới chỉ thử với Guest; chưa có fixture Customer/Staff/Admin (12 §2.4) vì `identity` chưa dựng.
- OpenAPI chưa khai báo response lỗi `ErrorDTO`: tách ticket [22](./22-openapi-error-responses.md).

#### Thay đổi theo yêu cầu

- Không

#### Review

| Mã | Chỗ | Kết luận | Lý do |
| --- | --- | --- | --- |
| T1 | `shared/tests/test_api_geo.py`, `test_load_geo.py` | đã sửa | dữ liệu test qua `shared/testing/factories.py` (02 §9.5) |
| T2 | `shared/tests/test_geo_api.py` | đã sửa | đổi tên `test_api_geo.py` (02 §9.2) |
| T3 | `shared/geo/models.py` | đã sửa | `Meta.db_table`, kèm `options` trong `0002_geo` |
| T4, T5, B5 | `shared/geo/api.py:18` | đã sửa | component `GeoDTO`, `maxLength` 10/255 (04 §5.6) |
| B6 | `shared/migrations/0002_geo.py:8` | đã sửa | bỏ `initial = True` |
| T15, B2 | `shared/tests/test_load_geo.py:20` | đã sửa | số đếm lấy từ package |
| B3 | `shared/tests/test_load_geo.py` | đã sửa | thêm test phường/xã chuyển tỉnh |
| T10, T12, B4 | `load_geo.py`, `selectors.py` | đã sửa | helper đệm mã, `unique_fields` theo PK, `province_exists` |
| P1 | `shared/geo/api.py` | chỉ báo | response lỗi trong OpenAPI là việc chung: ticket 22 |
| P2 | `backend/Makefile:50` | chỉ báo | máy không có `make`; chạy lệnh của recipe |
| P4 | `load_geo.py:33` | chỉ báo | cập nhật cả tỉnh của phường/xã: ghi vào Quyết định |
| T6 | `test_load_geo.py` | chỉ báo | giả lập package dữ liệu: ghi ngoại lệ vào Quyết định |
| B1, T7 | `selectors.py`, `test_api_geo.py` | chỉ báo | ghi ở Gap |
| T8 | `02-backend-structure.md` | chỉ báo | sửa ở phase sync |
| P5, B8, T11, T13, T14, B9, B10, T9 (`Refs:`) | nhiều chỗ | chỉ báo | smell hoặc tối ưu không cần cho MVP; mã luôn đệm đủ độ dài |
| P3, T9, B7 | commit `cd88bd6` | bác | đổi `Status:` 19–21 là triage người dùng chọn đầu phiên |

#### Tài liệu đã cập nhật

- `docs/architecture/02-backend-structure.md`: cây `shared/geo/` thêm `urls.py`, chữ ký selector; ghi chú `load_geo`, migration `0002_geo`, `ProvinceFactory`/`WardFactory`
- Ticket này: `## Quyết định` thêm cập nhật tỉnh của phường/xã, `db_table`, `GeoDTO`, mục Test (ngoại lệ giả lập package)
