# Báo cáo

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
- OpenAPI chưa khai báo response lỗi `ErrorDTO`: tách ticket [22](../22-openapi-error-responses/spec.md).

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
