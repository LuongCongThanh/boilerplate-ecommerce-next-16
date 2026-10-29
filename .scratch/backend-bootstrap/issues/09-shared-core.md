# Phần dùng chung của `shared`: model cơ sở, tiền, số điện thoại, HMAC, lỗi, logging

Status: ready-for-agent

Blocked by: 07

Spec: [spec.md](../spec.md)

Lớp API dùng chung tách sang ticket [16](./16-shared-api-layer.md), địa giới hành chính sang ticket [17](./17-shared-geo.md).

## Việc cần làm

- `shared/models.py`: `uuid7()` gọi `uuid.uuid7()`, `BaseModel` abstract (`id`, `created_at`, `updated_at`) theo [03 mục 0.1](../../../docs/architecture/03-data-model.md#01-cột-chung-và-khoá) và [ADR 0008](../../../docs/adr/0008-uuid-v7-primary-keys.md).
- `shared/money.py`: `Money(amount: int, currency="VND")`, từ chối float.
- `shared/phones.py`: `normalize_vn_phone` bằng `phonenumbers` theo [03 mục 0.6](../../../docs/architecture/03-data-model.md#06-chuẩn-hoá-số-điện-thoại).
- `shared/privacy.py`: `pii_hmac(value) -> "<kid>:<hex>"` với keyring `PII_HMAC_KEYS` ([ADR 0016](../../../docs/adr/0016-erasure-evidence-phone-hmac.md)).
- `shared/exceptions.py`: `DomainError(code, message, details)`, `RetryLater`.
- `shared/logging.py`: cấu hình structlog JSON, processor `redact_pii` ([02 mục 9.6](../../../docs/architecture/02-backend-structure.md#96-logging)).
- Migration `shared` bật `unaccent`, `pg_trgm`, `btree_gist` và tạo hàm `immutable_unaccent` ([03 mục 0.7](../../../docs/architecture/03-data-model.md#07-khởi-tạo-và-seed)).

## Acceptance criteria

- [ ] `0901234567` và `+84 901 234 567` cùng chuẩn hoá thành `+84901234567`; số không hợp lệ bị từ chối.
- [ ] `pii_hmac` cùng đầu vào cho cùng kết quả với cùng `kid`; đổi khoá đầu keyring thì giá trị mới mang `kid` mới.
- [ ] `Money` từ chối float.
- [ ] Log có key `email`, `phone`, `token` bị che.
- [ ] Sau migrate, ba extension và hàm `immutable_unaccent` có trong DB.
