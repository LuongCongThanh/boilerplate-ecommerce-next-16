# Hạ tầng dùng chung của `shared`: model cơ sở, tiền, số điện thoại, lỗi, API, logging, địa giới

Status: ready-for-agent

Blocked by: 07

Spec: [spec.md](../spec.md)

## Việc cần làm

- `shared/models.py`: `uuid7()` gọi `uuid.uuid7()`, `BaseModel` abstract (`id`, `created_at`, `updated_at`) theo [03 mục 0.1](../../../docs/architecture/03-data-model.md#01-cột-chung-và-khoá) và [ADR 0008](../../../docs/adr/0008-uuid-v7-primary-keys.md).
- `shared/money.py`: `Money(amount: int, currency="VND")`, từ chối float.
- `shared/phones.py`: `normalize_vn_phone` bằng `phonenumbers` theo [03 mục 0.6](../../../docs/architecture/03-data-model.md#06-chuẩn-hoá-số-điện-thoại).
- `shared/privacy.py`: `pii_hmac(value) -> "<kid>:<hex>"` với keyring `PII_HMAC_KEYS` ([ADR 0016](../../../docs/adr/0016-erasure-evidence-phone-hmac.md)).
- `shared/exceptions.py`: `DomainError(code, message, details)`, `RetryLater`.
- `shared/api/`: `exception_handler` trả `ErrorDTO` ([04 mục 3](../../../docs/architecture/04-api-contract.md#3-định-dạng-lỗi)), pagination (`page_size` mặc định 24, tối đa 100), `permissions` theo `kind`/`aud`, middleware `client_ip` (ADR 0009, so `X-BFF-Secret` bằng `hmac.compare_digest`, nhận tối đa hai secret), throttling cơ sở fail-open khi Redis lỗi, `i18n` theo `Accept-Language`.
- `shared/logging.py`: cấu hình structlog JSON, processor `redact_pii` ([02 mục 9.6](../../../docs/architecture/02-backend-structure.md#96-logging)).
- `shared/geo/`: model `Province`, `Ward` (mã chính thức làm PK), lệnh `load_geo` từ `vietnam-provinces` chạy lại an toàn, endpoint `GET store/geo/provinces` và `geo/provinces/{code}/wards`.
- Migration `shared` bật `unaccent`, `pg_trgm`, `btree_gist` và tạo hàm `immutable_unaccent` ([03 mục 0.7](../../../docs/architecture/03-data-model.md#07-khởi-tạo-và-seed)).

## Acceptance criteria

- [ ] `0901234567` và `+84 901 234 567` cùng chuẩn hoá thành `+84901234567`; số không hợp lệ bị từ chối.
- [ ] `pii_hmac` cùng đầu vào cho cùng kết quả với cùng `kid`; đổi khoá đầu keyring thì giá trị mới mang `kid` mới.
- [ ] Mọi lỗi không bắt (kể cả 404, 405, lỗi validate của DRF) trả đúng shape `ErrorDTO` có `request_id`.
- [ ] Thiếu hoặc sai `X-BFF-Secret` thì throttle dùng IP kết nối; đúng secret thì dùng `X-Client-IP`.
- [ ] Redis tắt thì request vẫn qua throttle (fail-open) và có log cảnh báo không chứa IP thô.
- [ ] `make load-geo` chạy hai lần liên tiếp không lỗi, không trùng dữ liệu; endpoint địa giới trả array không phân trang.
- [ ] Log có key `email`, `phone`, `token` bị che.
