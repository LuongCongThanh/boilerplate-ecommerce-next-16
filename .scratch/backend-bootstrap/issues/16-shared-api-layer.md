# Lớp API dùng chung: định dạng lỗi, phân trang, quyền, IP client, throttling, i18n

Status: ready-for-agent

Blocked by: 09

Spec: [spec.md](../spec.md)

Tách từ ticket [09](./09-shared-core.md).

## Việc cần làm

- `shared/api/`:
  - `exception_handler` trả `ErrorDTO` ([04 mục 3](../../../docs/architecture/04-api-contract.md#3-định-dạng-lỗi)).
  - Pagination: `page_size` mặc định 24, tối đa 100.
  - `permissions` theo `kind`/`aud`.
  - Middleware `client_ip` (ADR 0009): so `X-BFF-Secret` bằng `hmac.compare_digest`, nhận tối đa hai secret.
  - Throttling cơ sở, fail-open khi Redis lỗi.
  - `i18n` theo `Accept-Language`.

## Acceptance criteria

- [ ] Mọi lỗi không bắt (kể cả 404, 405, lỗi validate của DRF) trả đúng shape `ErrorDTO` có `request_id`.
- [ ] Thiếu hoặc sai `X-BFF-Secret` thì throttle dùng IP kết nối; đúng secret thì dùng `X-Client-IP`.
- [ ] Redis tắt thì request vẫn qua throttle (fail-open) và có log cảnh báo không chứa IP thô.
- [ ] `page_size` lớn hơn 100 bị giới hạn ở 100.
