# Khai báo `ErrorDTO` và response lỗi trong OpenAPI

Status: needs-triage

Spec: [spec.md](../spec.md)

Tách từ ticket [17](./17-shared-geo.md) khi review ngày 30/10/2026.

## Bối cảnh

[04 mục 5.6](../../../docs/architecture/04-api-contract.md) yêu cầu mỗi operation khai báo request, response, status, permission và error schema trong OpenAPI. Mọi lỗi API đã trả `ErrorDTO` qua `shared.api.exception_handler` (ticket 16), nhưng schema do drf-spectacular sinh chưa có component `ErrorDTO` và chưa operation nào khai báo response lỗi. Ví dụ `GET store/geo/provinces/{code}/wards` của ticket 17 trả 404 `ErrorDTO` nhưng OpenAPI chỉ ghi `200`.

## Việc cần làm

- Thêm component `ErrorDTO` (`{error: {code, message, details, request_id}}`, 04 mục 5.1) vào schema.
- Chọn cách gắn response lỗi cho operation (mặc định qua hook hoặc `AutoSchema` riêng, hay khai báo từng view bằng `extend_schema`), áp cho endpoint địa giới hiện có.
- Làm trước hoặc cùng ticket [03](./03-openapi-schema-drift-check.md) để `openapi.yaml` commit lần đầu đã có `ErrorDTO`.

## Acceptance criteria

- [ ] `manage.py spectacular --validate` sinh schema có component `ErrorDTO` đúng 04 mục 5.1.
- [ ] Endpoint địa giới khai báo response 404 dạng `ErrorDTO` cho `geo/provinces/{code}/wards` và các status lỗi chung (400, 429, 500) theo cách đã chọn.
