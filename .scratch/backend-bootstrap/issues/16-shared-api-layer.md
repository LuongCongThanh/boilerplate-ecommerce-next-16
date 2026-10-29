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
| `page_size` | Lớn hơn 100 thì giới hạn ở 100 (theo AC4); nhỏ hơn 1 hoặc không phải số → `400 VALIDATION_ERROR`; `page` cũng vậy (thêm khi review); trang vượt quá cuối → `404 NOT_FOUND`. Khác [04 mục 5.1](../../../docs/architecture/04-api-contract.md) (ghi `page_size` ngoài 1..100 trả 400): sửa tài liệu 04 cho khớp |
| Mã lỗi | 405 → `METHOD_NOT_ALLOWED` (04 chưa có mã cho 405, thêm vào tài liệu). `APIException` khác của DRF dùng `default_code` viết hoa. `DomainError` dùng `code`, `http_status`, `message`, `details` của lớp. Exception không bắt → `500 INTERNAL_ERROR`, không lộ chi tiết. Route lạ và lỗi ngoài DRF đi qua `handler400` (`BAD_REQUEST`), `handler403` (`PERMISSION_DENIED`), `handler404`, `handler500` của Django; hai handler đầu thêm khi review |
| `request_id` | Lấy từ contextvars mà `django-structlog` đã gắn. Dùng `X-Request-ID` từ BFF tách sang ticket [19](./19-trust-upstream-request-id.md) |
| Quyền mặc định | `DEFAULT_PERMISSION_CLASSES = [IsAuthenticated]` ngay từ M0 ([05 mục 4](../../../docs/architecture/05-auth-security.md)); view schema/docs khai báo `AllowAny`. `IsCustomer`, `IsStaff`, `IsAdmin` đọc `kind` từ `request.user` và `aud` từ `request.auth`; thiếu một trong hai thì từ chối. `IsOrderOwner` thuộc `modules/ordering` |
| `BFF_SHARED_SECRET` | Chuỗi cách nhau bằng dấu phẩy, 1 hoặc 2 secret không rỗng; sai thì `config/env.py` báo lỗi lúc khởi động |
| `client_ip` | Middleware gán IP lên request; nơi khác đọc qua `get_client_ip(request)`. `django-structlog` không gắn IP vào log (`DJANGO_STRUCTLOG_IP_LOGGING_ENABLED = False`, thêm khi review). Secret khớp (`hmac.compare_digest` với từng secret) và `X-Client-IP` là IPv4/IPv6 hợp lệ thì dùng `X-Client-IP`; ngược lại dùng `REMOTE_ADDR`. Secret đúng mà IP sai định dạng thì log cảnh báo, không ghi giá trị |
| Throttling | `AnonThrottle` 120/phút và `AccountThrottle` 300/phút trên một lớp cơ sở fail-open; khoá là `pii_hmac(client_ip)`, không bao giờ là IP thô. Cache lỗi thì cho request qua và log `throttle_backend_unavailable` chỉ kèm scope. Scope riêng (`checkout`, `order_lookup`, …) thêm ở mốc dùng tới |
| i18n | Chỉ bật `LocaleMiddleware` để `Accept-Language` chọn ngôn ngữ (mặc định `vi`). Chưa tạo bản dịch tiếng Anh; không cần file `shared/api/i18n.py` riêng |

## Acceptance criteria

- [ ] Mọi lỗi không bắt (kể cả 404, 405, lỗi validate của DRF) trả đúng shape `ErrorDTO` có `request_id`.
- [ ] Thiếu hoặc sai `X-BFF-Secret` thì throttle dùng IP kết nối; đúng secret thì dùng `X-Client-IP`.
- [ ] Redis tắt thì request vẫn qua throttle (fail-open) và có log cảnh báo không chứa IP thô.
- [ ] `page_size` lớn hơn 100 bị giới hạn ở 100.

## Comments

### Báo cáo 29/10/2026

**Nhánh:** `feat/shared-api-layer` · **PR:** chưa mở · **Mode:** full

#### Đã làm

| AC | Bằng chứng |
| --- | --- |
| 1. Mọi lỗi không bắt trả `ErrorDTO` có `request_id` | `shared/tests/test_api_errors.py::test_unknown_route_returns_error_dto`, `::test_method_not_allowed_returns_error_dto`, `::test_validation_error_returns_fields`, `::test_domain_error_uses_class_status`, `::test_unhandled_exception_returns_internal_error` |
| 2. Thiếu/sai `X-BFF-Secret` → IP kết nối; đúng → `X-Client-IP` | `shared/tests/test_api_client_ip.py::test_missing_secret_uses_remote_addr`, `::test_wrong_secret_uses_remote_addr`, `::test_valid_secret_uses_x_client_ip`, `::test_second_secret_accepted` |
| 3. Redis tắt → fail-open, log không chứa IP thô | `shared/tests/test_api_throttling.py::test_cache_down_allows_request_and_logs_without_ip`, `::test_cache_down_json_log_has_no_raw_ip` (chạy qua chuỗi processor JSON thật), `::test_cache_down_allows_authenticated_request` |
| 4. `page_size` > 100 giới hạn ở 100 | `shared/tests/test_api_pagination.py::test_page_size_capped_at_100` |

Test thêm ngoài AC: quyền `IsCustomer`/`IsStaff`/`IsAdmin` (`test_api_permissions.py`), quyền mặc định chặn người chưa xác thực, schema vẫn công khai, 429 giữ `Retry-After`, lỗi 400/403 ngoài DRF, `page` sai kiểu → 400, `Accept-Language` (`test_api_i18n.py`), IP sai định dạng, quota tách theo IP, `BFF_SHARED_SECRET` 1–2 giá trị (`tests/test_env.py`).

Lint xanh (ruff, format, mypy, import-linter) · test: 138 passed trong 6.96s. Chạy từng lệnh trong `Makefile` vì máy chưa có `make`.

#### Chưa làm

- Metric khi throttle fail-open (05 mục 5, 10-nfr): hiện chỉ có log `throttle_backend_unavailable`. Metric thêm khi dựng observability.
- Scope throttle riêng (`checkout`, `order_lookup`, `auth_google`, …): thêm ở mốc dùng tới, theo quyết định.
- Bản dịch tiếng Anh cho message lỗi: chỉ bật `LocaleMiddleware`, theo quyết định.

#### Gap

- Chưa có authenticator, nên tới M1 request chưa xác thực nhận `403 PERMISSION_DENIED` thay vì `401 NOT_AUTHENTICATED`. M1 thêm JWT authentication sẽ sửa.
- View mới phải khai báo quyền; mặc định là `IsAuthenticated`. View công khai phải ghi `AllowAny`.
- Throttle scope mới nên kế thừa `ClientIpRateThrottle` hoặc `FailOpenRateThrottle` để có fail-open và khoá `pii_hmac`.
- Đã tắt `DJANGO_STRUCTLOG_IP_LOGGING_ENABLED` cho mọi log request, không riêng throttle. Cần tra theo IP thì sau này log `pii_hmac(client_ip)`.
- Tin `X-Request-ID` từ BFF: ticket [19](./19-trust-upstream-request-id.md) (`needs-triage`).

#### Thay đổi theo yêu cầu

- Không

#### Review

Một vòng sửa, tất cả finding đã sửa.

| Mã | Chỗ | Kết luận | Lý do |
| --- | --- | --- | --- |
| SP1 | `config/settings/base.py` | đã sửa | `django-structlog` gắn `ip` thô vào mọi log; tắt `DJANGO_STRUCTLOG_IP_LOGGING_ENABLED`, test qua chuỗi processor thật |
| SP2 | `shared/api/views.py`, `config/urls.py` | đã sửa | Thêm `handler400` (`BAD_REQUEST`) và `handler403` (`PERMISSION_DENIED`) |
| SP3 | `shared/api/pagination.py` | đã sửa | `page` sai kiểu hoặc < 1 → 400, theo 04 mục 5.1 |
| SP4 | `shared/tests/test_api_i18n.py` | đã sửa | Thêm test `Accept-Language` |
| SP5 | `shared/tests/test_api_pagination.py` | đã sửa | Kiểm đủ shape `ErrorDTO` |
| SP6 | throttling | chỉ báo | Chưa có metric khi fail-open, xem *Chưa làm* |
| SP7 | nhiều chỗ | bác | Phần làm thêm nhỏ, có lý do |
| ST1 | `shared/api/pagination.py` | đã sửa | Bọc `gettext_lazy` |
| ST2 | `backend/conftest.py` | đã sửa | Fixture chuyển sang `shared/testing/fixtures.py` (12 mục fixture) |
| ST3 | `docs/architecture/02-backend-structure.md` | đã sửa | Cây thư mục khớp code |
| ST4–8 | `shared/api/throttling.py`, `client_ip.py`, test | đã sửa | Bỏ con số rate trong docstring; thêm `get_client_ip()`; gom helper test; `/items` → `/paged`; test giữ các `handlerXXX` khớp nhau |

#### Tài liệu đã cập nhật

- `docs/architecture/04-api-contract.md`: `page_size` > 100 giới hạn ở 100; `page` sai kiểu → 400; thêm mã `METHOD_NOT_ALLOWED` (405) và `BAD_REQUEST` (400 ngoài DRF).
- `docs/architecture/02-backend-structure.md`: cây `shared/api` (bỏ `i18n.py`, thêm `views.py`), `shared/testing/fixtures.py`, mô tả `conftest.py`; mục context log ghi không gắn IP.
- `docs/architecture/08-local-development.md` và `.env.example`: `BFF_SHARED_SECRET` nhận 1–2 secret cách nhau bằng dấu phẩy.
