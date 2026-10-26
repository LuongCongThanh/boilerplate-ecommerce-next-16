# 12. Chiến lược test

> Trạng thái: **Bản nháp chờ review**. Phạm vi: chỉ backend Django. Frontend Next.js là repo riêng ([ADR 0001](../adr/0001-nextjs-frontend-django-api.md)) và tự có chiến lược test; ở đây chỉ nói phần backend cam kết với frontend (OpenAPI, mục 5).

Quy ước viết code test (factory, mock, thời gian) nằm ở [02-backend-structure.md](./02-backend-structure.md) mục 9.5. Cách chạy test ở máy local xem [08-local-development.md](./08-local-development.md) mục 5.

## 1. Nguyên tắc

- Test chạy trên **PostgreSQL thật** (`fashion_test`), không dùng SQLite và không mock ORM. Lý do: nghiệp vụ dựa vào `select_for_update`, `EXCLUDE`, `unaccent`.
- Chỉ giả lập **hệ thống bên ngoài**: Fake Gateway cho thanh toán và vận chuyển ([ADR 0005](../adr/0005-provider-adapters-fake-gateways.md)), `respx` cho `httpx`. CI không gọi sandbox thật của VNPay, MoMo, GHN (mục 7).
- Celery chạy đồng bộ (`CELERY_TASK_ALWAYS_EAGER=True` trong `settings/test.py`); thời gian cố định bằng `time-machine`.
- Nghiệp vụ được test ở tầng **service**. Tầng API chỉ test những gì thuộc về HTTP, không test lại nghiệp vụ.
- Repo là public: dữ liệu mẫu phải là giá trị giả rõ ràng ([11-git-workflow.md](./11-git-workflow.md) mục 8).

## 2. Các loại test

Xếp theo số lượng, từ nhiều đến ít. Hàm thuần không cần DB (ví dụ `Money`, kiểm tra chữ ký) không có loại riêng, mà xếp vào loại của module chứa nó.

| # | Loại | Đặt ở | Kiểm tra gì |
|---|---|---|---|
| 1 | Service | `modules/<module>/tests/test_services_<chủ đề>.py` | Business rule, chuyển trạng thái, sự kiện ghi vào outbox |
| 2 | Concurrency | `modules/<module>/tests/test_concurrency_<chủ đề>.py` | Không bán vượt Tồn kho, không vượt lượt Voucher, không deadlock |
| 3 | Handler và outbox | `modules/<module>/tests/test_handlers.py`, `shared/events/tests/` | Handler idempotent, relay gửi đúng và gửi lại được |
| 4 | API | `modules/<module>/tests/test_api_<store\|backoffice\|webhooks>.py` | Phân quyền, định dạng lỗi, `Idempotency-Key`, throttle, N+1 query |
| 5 | Bảo mật auth/JWT | `modules/identity/tests/test_services_tokens.py` | Theo OWASP JWT Cheat Sheet |
| 6 | Adapter nhà cung cấp | `modules/<payments\|shipping>/tests/test_providers_<tên>.py` | Chữ ký VNPay/MoMo, gọi HTTP lỗi, IPN bất thường |
| 7 | Flow xuyên module | `backend/tests/flows/test_<flow>_flow.py` | Một luồng nghiệp vụ đi hết từ đầu đến cuối qua HTTP |

Ngoài pytest, CI còn có các **cổng kiểm tra tĩnh** (mục 8).

### 2.1. Service

- Mỗi hàm service có ít nhất 1 test cho trường hợp chạy đúng và 1 test cho mỗi lỗi nghiệp vụ nó ném ra.
- Test nào kiểm tra một quy tắc trong [04-business-rules.md](../business/04-business-rules.md) thì gắn marker `br` (mục 3).
- Kiểm tra sự kiện: service ghi đúng sự kiện vào outbox, và khi service lỗi thì không có sự kiện nào được ghi (cùng transaction).
- Mốc thời gian (Giữ hàng 15 phút, Hoàn tất sau 7 ngày, Đổi trả trong 7 ngày) dùng `time-machine`, test cả hai phía của mốc.

```python
@pytest.mark.br("BR-INV-03")
def test_reserve_stock_fails_when_stock_is_insufficient(stock_item_factory):
    ...
```

### 2.2. Concurrency

Test dùng `@pytest.mark.django_db(transaction=True)` và `@pytest.mark.concurrency`. Mỗi test chạy N thread, mỗi thread mở kết nối DB riêng, các thread xuất phát cùng lúc nhờ `threading.Barrier`, rồi kiểm tra bất biến sau khi tất cả kết thúc. Test chạy trong **mọi PR**, vì mỗi worker của `pytest-xdist` đã có DB riêng.

Bắt buộc có 3 test:

| Kịch bản | Bất biến |
|---|---|
| N khách cùng Giữ hàng hoặc trừ Tồn kho cho K cái cuối cùng của một Biến thể (N > K) | Đúng K lần thành công, N − K lần ném `OUT_OF_STOCK`, Tồn kho không âm |
| N khách cùng dùng một Voucher còn K lượt | Đúng K lượt được dùng, không vượt `usage_limit` |
| Hai Đơn hàng cùng chứa 2 Biến thể nhưng thứ tự Dòng đơn hàng ngược nhau | Cả hai hoàn tất, không deadlock (khoá theo thứ tự `variant_id`) |

### 2.3. Handler và outbox

- Mỗi handler: gọi 2 lần với cùng một sự kiện thì chỉ xử lý 1 lần (`ProcessedEvent`).
- Relay: chỉ đọc sự kiện chưa gửi, đánh dấu `dispatched_at` sau khi gửi, gửi lại được khi lần trước lỗi.
- Job Celery Beat ([07-async-events-jobs.md](./07-async-events-jobs.md) mục 3.2): chạy 2 lần liên tiếp cho ra cùng kết quả.

### 2.4. API

- **Phân quyền**: mỗi endpoint thử với Guest, Customer, Staff, Admin (theo cột quyền trong [04-api-contract.md](./04-api-contract.md)); Khách hàng này không xem được Đơn hàng của Khách hàng khác.
- **Lỗi**: đúng mã HTTP và đúng định dạng lỗi chuẩn (400, 401, 403, 404, 409, 429).
- **`Idempotency-Key`**: thiếu key; gửi lại cùng key thì nhận lại đúng kết quả cũ; cùng key nhưng body khác thì ra `IDEMPOTENCY_CONFLICT`.
- **Throttle**: endpoint có throttle chặt (ví dụ `orders/lookup`) trả `429` khi vượt ngưỡng.
- **N+1 query**: `django-zeal` bật cho toàn bộ test; test fail nếu có N+1.

### 2.5. Bảo mật auth/JWT

Theo [05-auth-security.md](./05-auth-security.md) mục 9 và [ADR 0002](../adr/0002-auth-nextauth-session-django-jwt.md): sai thuật toán, `alg: none`, sai `aud`, hết hạn, sai `kid`, dùng lại refresh token (phải thu hồi cả chuỗi), đổi `token_version`, thu hồi qua `jti`, token storefront không dùng được cho back-office.

### 2.6. Adapter nhà cung cấp

- **Chữ ký VNPay (HMAC-SHA512) và MoMo (HMAC-SHA256)**: unit test với dữ liệu mẫu lấy từ tài liệu của nhà cung cấp, gồm chữ ký đúng, sai một ký tự, thiếu field. Fake Gateway không kiểm tra chữ ký nên test này là nơi duy nhất bảo vệ phần đó.
- **Gọi HTTP** bằng `respx`: timeout, lỗi 5xx, response sai định dạng; GHN lỗi thì dùng phí ship dự phòng.
- **IPN và webhook**: gọi trùng, sai chữ ký, sai số tiền, đến muộn sau khi đơn đã bị huỷ.

### 2.7. Flow xuyên module

Flow test gọi qua **HTTP** (`api_client`, `staff_client`, endpoint IPN của Fake Gateway), để đi qua đúng auth, `Idempotency-Key` và serializer như thực tế. Các bước do Celery Beat kích hoạt thì dùng `time-machine` để vượt mốc thời gian, rồi gọi thẳng task (ví dụ `ordering.cancel_expired_pending_orders`, `ordering.complete_delivered_orders`). Đánh dấu bằng `@pytest.mark.flow`.

Bắt buộc có 6 flow:

| Flow | Nội dung |
|---|---|
| `test_cod_checkout_flow.py` | Checkout COD → giao → Đã giao → Hoàn tất sau 7 ngày |
| `test_online_payment_success_flow.py` | Checkout online → Giữ hàng → IPN thành công → trừ Tồn kho → giao → Hoàn tất |
| `test_online_payment_failure_flow.py` | IPN thất bại, hoặc Giữ hàng hết hạn sau 15 phút → Tồn kho và lượt Voucher được trả lại |
| `test_cancel_paid_order_flow.py` | Huỷ Đơn hàng đã thanh toán online → Hoàn tiền về đúng cổng |
| `test_returned_to_sender_flow.py` | Giao thất bại → Hoàn hàng → nhập lại Tồn kho |
| `test_return_refund_flow.py` | Đổi trả được chấp nhận → Hoàn tiền; Đơn hàng chỉ Hoàn tất khi không còn Đổi trả nào mở |

## 3. Marker của pytest

Khai báo trong `pyproject.toml` (`--strict-markers`):

| Marker | Ý nghĩa | Dùng để |
|---|---|---|
| `br("BR-XXX-NN", ...)` | Test kiểm tra một hay nhiều business rule | Lọc test theo quy tắc; `make br-report` |
| `concurrency` | Test chạy nhiều thread, cần `transaction=True` | `pytest -m concurrency` |
| `flow` | Flow xuyên module | `pytest -m flow` |

`make br-report` liệt kê các mã `BR-xxx` trong `04-business-rules.md` chưa có test nào gắn marker `br`. Lệnh này chỉ để xem, **không** chặn CI, vì nhiều quy tắc chưa có code.

## 4. Dữ liệu test và ranh giới module

- Dữ liệu test tạo bằng `factory-boy`, không dùng fixture JSON. Fixture pytest dùng chung (`api_client`, `staff_client`…) ở `shared/testing/fixtures.py`.
- Mỗi module để factory ở `modules/<module>/tests/factories.py`.
- Test trong một module chỉ dùng factory của chính module đó và của các module lớp dưới, theo đúng chiều phụ thuộc trong [02-backend-structure.md](./02-backend-structure.md) mục 4. Ví dụ test của `ordering` dùng được factory của `catalog` và `inventory`; test của `inventory` không dùng được factory của `ordering`.
- `backend/tests/flows/` được dùng factory của mọi module.
- `import-linter` giữ quy tắc này (mục 8).

## 5. Hợp đồng API với frontend (OpenAPI)

- Schema được commit tại `backend/openapi.yaml`, sinh bằng `manage.py spectacular --validate --file openapi.yaml`. Frontend sinh TS client từ file này.
- CI sinh lại schema và fail nếu khác file đã commit. Vì vậy mọi thay đổi API đều hiện trong diff của PR.
- Chưa dùng công cụ phát hiện breaking change (`oasdiff`). Reviewer tự đọc diff của `openapi.yaml`; diff có xoá field hay endpoint thì PR phải nêu rõ và báo cho frontend.

## 6. Migration

- Migration chỉ đổi schema: không cần test; `makemigrations --check` và kiểm tra trùng số trong CI là đủ.
- Data migration (có `RunPython`): bắt buộc có test bằng `django-test-migrations`, chạy migration trên dữ liệu mẫu rồi kiểm tra kết quả.

## 7. Sandbox thật của nhà cung cấp

CI không gọi sandbox thật, vì repo là public (không đưa secret sandbox vào CI) và sandbox của nhà cung cấp hay lỗi ngẫu nhiên. Kiểm tra với sandbox VNPay, MoMo, GHN là **checklist chạy tay trên staging trước mỗi release**, theo kịch bản ở [06-integrations.md](./06-integrations.md) mục 8.

## 8. Cổng chặn trong CI

Job `backend` trong `.github/workflows/ci.yml`:

| Cổng | Điều kiện để qua |
|---|---|
| `ruff check`, `ruff format --check` | Không lỗi |
| `mypy` | Không lỗi (`--strict` cho `services`, `selectors`, `contracts`) |
| `lint-imports` | Không vi phạm ranh giới module, kể cả quy tắc factory (mục 4) |
| `pytest` | Toàn bộ test qua, kể cả `concurrency` và `flow` |
| Coverage | ≥ 80% cho `modules/*/services` (`coverage report --include="modules/*/services/*" --fail-under=80`). **Không** đặt ngưỡng cho toàn repo, để không ai phải viết test chỉ để lấp số |
| Migration | `makemigrations --check`, không trùng số |
| OpenAPI | Schema sinh ra trùng với `backend/openapi.yaml` |
| `pip-audit` | Không có lỗ hổng |

## 9. Chưa làm ở MVP

| Việc | Khi nào làm |
|---|---|
| Test tải theo [10-nfr.md](./10-nfr.md) mục 1 (p95 300/800 ms, 50 request/giây khi khuyến mãi), chạy bằng k6 trên staging | Trước đợt khuyến mãi lớn đầu tiên |
| `oasdiff` phát hiện breaking change của OpenAPI | Khi API có client ngoài frontend của team (ví dụ mobile app) |
| E2E qua trình duyệt | Thuộc repo frontend |

Ở MVP, hiệu năng chỉ được bảo vệ bằng `django-zeal` (N+1 query) và test concurrency (mục 2.2).
