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

## Quyết định

Chốt khi grilling ngày 29/10/2026.

| Chủ đề | Quyết định |
|---|---|
| `page_size` | Lớn hơn 100 thì giới hạn ở 100 (theo AC4); nhỏ hơn 1 hoặc không phải số → `400 VALIDATION_ERROR`; trang vượt quá cuối → `404 NOT_FOUND`. Khác [04 mục 5.1](../../../docs/architecture/04-api-contract.md) (ghi `page_size` ngoài 1..100 trả 400): sửa tài liệu 04 cho khớp |
| Mã lỗi | 405 → `METHOD_NOT_ALLOWED` (04 chưa có mã cho 405, thêm vào tài liệu). `APIException` khác của DRF dùng `default_code` viết hoa. `DomainError` dùng `code`, `http_status`, `message`, `details` của lớp. Exception không bắt → `500 INTERNAL_ERROR`, không lộ chi tiết. Route lạ và lỗi ngoài DRF đi qua `handler404`/`handler500` của Django |
| `request_id` | Lấy từ contextvars mà `django-structlog` đã gắn. Dùng `X-Request-ID` từ BFF tách sang ticket [19](./19-trust-upstream-request-id.md) |
| Quyền mặc định | `DEFAULT_PERMISSION_CLASSES = [IsAuthenticated]` ngay từ M0 ([05 mục 4](../../../docs/architecture/05-auth-security.md)); view schema/docs khai báo `AllowAny`. `IsCustomer`, `IsStaff`, `IsAdmin` đọc `kind` từ `request.user` và `aud` từ `request.auth`; thiếu một trong hai thì từ chối. `IsOrderOwner` thuộc `modules/ordering` |
| `BFF_SHARED_SECRET` | Chuỗi cách nhau bằng dấu phẩy, 1 hoặc 2 secret không rỗng; sai thì `config/env.py` báo lỗi lúc khởi động |
| `client_ip` | Middleware gán `request.client_ip`. Secret khớp (`hmac.compare_digest` với từng secret) và `X-Client-IP` là IPv4/IPv6 hợp lệ thì dùng `X-Client-IP`; ngược lại dùng `REMOTE_ADDR`. Secret đúng mà IP sai định dạng thì log cảnh báo, không ghi giá trị |
| Throttling | `AnonThrottle` 120/phút và `AccountThrottle` 300/phút trên một lớp cơ sở fail-open; khoá là `pii_hmac(client_ip)`, không bao giờ là IP thô. Cache lỗi thì cho request qua và log `throttle_backend_unavailable` chỉ kèm scope. Scope riêng (`checkout`, `order_lookup`, …) thêm ở mốc dùng tới |
| i18n | Chỉ bật `LocaleMiddleware` để `Accept-Language` chọn ngôn ngữ (mặc định `vi`). Chưa tạo bản dịch tiếng Anh; không cần file `shared/api/i18n.py` riêng |

## Acceptance criteria

- [ ] Mọi lỗi không bắt (kể cả 404, 405, lỗi validate của DRF) trả đúng shape `ErrorDTO` có `request_id`.
- [ ] Thiếu hoặc sai `X-BFF-Secret` thì throttle dùng IP kết nối; đúng secret thì dùng `X-Client-IP`.
- [ ] Redis tắt thì request vẫn qua throttle (fail-open) và có log cảnh báo không chứa IP thô.
- [ ] `page_size` lớn hơn 100 bị giới hạn ở 100.
