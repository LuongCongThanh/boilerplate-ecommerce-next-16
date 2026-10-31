# Báo cáo

### Báo cáo 29/10/2026

**Nhánh:** `feat/shared-api-layer` · **PR:** #24 · **Mode:** full

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
- Tin `X-Request-ID` từ BFF: ticket [19](../19-trust-upstream-request-id/spec.md) (`needs-triage`).

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
