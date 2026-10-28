# 12. Chiến lược test

> Trạng thái: **Bản nháp chờ review**. Phạm vi: chỉ backend Django. Frontend Next.js là repo riêng ([ADR 0001](../adr/0001-nextjs-frontend-django-api.md)) và tự có chiến lược test; ở đây chỉ nói phần backend cam kết với frontend (OpenAPI, mục 5).

Quy ước viết code test (factory, mock, thời gian) nằm ở [02-backend-structure.md](./02-backend-structure.md) mục 9.5. Cách chạy test ở máy local xem [08-local-development.md](./08-local-development.md) mục 5.

## 1. Nguyên tắc

- Test chạy trên **PostgreSQL thật** (`fashion_test`), không dùng SQLite và không mock ORM. Lý do: nghiệp vụ dựa vào `select_for_update`, `EXCLUDE`, `unaccent`.
- Chỉ giả lập **hệ thống bên ngoài**: Fake Gateway cho thanh toán và vận chuyển ([ADR 0005](../adr/0005-provider-adapters-fake-gateways.md)), `respx` cho `httpx`. Fake Gateway và `FakeShippingProvider` được bật bằng `FAKE_PROVIDERS_ENABLED=true` trong `settings/test.py` (cùng cờ với local), nên flow test gọi được trang và endpoint IPN của Fake Gateway. CI không gọi sandbox thật của VNPay, MoMo, GHN (mục 7).
- Celery chạy đồng bộ (`CELERY_TASK_ALWAYS_EAGER=True` trong `settings/test.py`); thời gian cố định bằng `time-machine`.
- Test chạy trong transaction không bao giờ commit, nên task đẩy bằng `shared.tasks.enqueue_on_commit` không tự chạy, và relay (một tiến trình riêng) không tự gửi sự kiện. Test service cần task chạy thì dùng `django_capture_on_commit_callbacks(execute=True)`; flow test dùng `drain_events()` (mục 2.7).
- Nghiệp vụ được test ở tầng **service**. Tầng API chỉ test những gì thuộc về HTTP, không test lại nghiệp vụ.
- Repo là public: dữ liệu mẫu phải là giá trị giả rõ ràng ([11-git-workflow.md](./11-git-workflow.md) mục 8).

## 2. Các loại test

Xếp theo số lượng, từ nhiều đến ít. Hàm thuần không cần DB (ví dụ `Money`, kiểm tra chữ ký) không có loại riêng, mà xếp vào loại của module chứa nó.

| # | Loại | Đặt ở | Kiểm tra gì |
|---|---|---|---|
| 1 | Service | `modules/<module>/tests/test_services_<chủ đề>.py` | Business rule, chuyển trạng thái, sự kiện ghi vào outbox |
| 2 | Concurrency | `modules/<module>/tests/test_concurrency_<chủ đề>.py` | Không bán vượt Tồn kho, không vượt lượt Voucher, không deadlock |
| 3 | Handler và outbox | `modules/<module>/tests/test_handlers_<chủ đề>.py`, `shared/events/tests/` | Mỗi sự kiện chỉ xử lý một lần, sự kiện tới sai thứ tự, consumer xử lý đúng từng loại lỗi, relay gửi đúng và gửi lại được |
| 4 | API | `modules/<module>/tests/test_api_<store\|backoffice\|webhooks>.py` | Phân quyền, `X-Lookup-Token`, định dạng lỗi, `Idempotency-Key`, throttle theo `X-Client-IP`, N+1 query |
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

Ngoài quy tắc chung, bắt buộc có các test service sau, vì đây là những chỗ dễ sai:

| Kịch bản | Kỳ vọng |
|---|---|
| Tổng tính lại khác `expected_total` (Giá khuyến mãi vừa hết hạn, Voucher vừa hết lượt) (BR-ORD-07) | Ném `PriceChanged` (`PRICE_CHANGED`) kèm bảng tính mới; không tạo đơn, không Giữ hàng, không tính lượt Voucher |
| Phân bổ Voucher về Dòng đơn hàng | Tổng `voucher_discount` của các dòng bằng đúng số giảm của Voucher; phần lẻ dồn vào dòng cuối |
| Hoàn tiền khi Đổi trả một phần có Voucher (BR-RET-07) | Đơn 3 × 200.000đ, Voucher giảm 60.000đ, được miễn phí ship; trả 1 áo → hoàn 180.000đ, không truy thu phí ship |
| Giới hạn lượt dùng Voucher mỗi người (BR-VCH-07) | Khách hàng đã dùng hết lượt rồi đặt tiếp như Khách vãng lai bằng cùng số điện thoại → Voucher bị từ chối |
| Staff huỷ đơn PACKING khi Vận đơn requested hoặc creation_unknown (T9) | Ném SHIPMENT_IN_PROGRESS, giữ PACKING; không cho bàn giao lại để tạo mã mới |
| Thanh toán của đơn COD | T2 tạo Thanh toán COD `pending`; T11 chuyển `succeeded`; huỷ đơn hoặc Hoàn hàng chuyển `cancelled`. Không thao tác nào ghi `payments.payment-succeeded` vào outbox, nên đơn COD giao xong không bị tạo Hoàn tiền |
| Hàng chờ xuất (BR-INV-10) | Đặt đơn COD: Tồn kho giảm, Hàng chờ xuất tăng đúng số lượng; T10 xoá Hàng chờ xuất; huỷ trước Bàn giao (T7, T9) trả Hàng chờ xuất về Tồn kho |
| Kiểm kê (BR-INV-12) | Tồn kho 7, Hàng chờ xuất 3, số đếm 10 → không điều chỉnh; số đếm 9 → điều chỉnh −1 loại `stock_count` |
| Điều chỉnh giảm vượt Số lượng bán được (BR-INV-11) | Ném `INSUFFICIENT_AVAILABLE`; Tồn kho không đổi |
| Chấp nhận Đổi trả một phần (BR-RET-08) | Chỉ phần `accepted_quantity` của dòng `restock = true` được cộng lại Tồn kho; Hoàn tiền tính trên số lượng được chấp nhận; không dòng nào được chấp nhận thì yêu cầu `rejected` |
| Doanh thu khi Người mua trả tiền hai lần (BR-REV-01) | Hoàn tiền theo BR-PAY-05 không bị trừ; Doanh thu của đơn bằng Tổng tiền đơn |
| Đặt đơn vãng lai bằng email của Tài khoản đã xác thực (BR-ORD-08) | Đơn có `customer_id` ngay khi tạo |
| Hạ Giá bán xuống ≤ Giá khuyến mãi đang hoặc sắp hiệu lực (BR-PRC-05) | Ném `LIST_PRICE_BELOW_SALE_PRICE`; Giá bán không đổi |
| Giá, snapshot, trạng thái bán hoặc SalePrice đổi sau lần đọc báo giá ngoài transaction | Checkout kiểm tra lại dưới khoá Variant; rollback Order, Giữ hàng và lượt Voucher; trả PRICE_CHANGED với quote mới dù tổng tiền tình cờ không đổi |
| Xoá dữ liệu có một handler chưa xong, failed, rejected hoặc chưa có delivery | ErasureRequest giữ processing, completed_at null; không coi danh sách delivery rỗng là thành công |
| Tất cả handler ẩn danh bắt buộc completed | Job hoàn tất một lần; gọi lại không phát thêm sự kiện; subject còn lấy được trong processing và được làm sạch sau hoàn tất |

### 2.2. Concurrency

Test dùng `@pytest.mark.django_db(transaction=True)` và `@pytest.mark.concurrency`. Mỗi test chạy N thread, mỗi thread mở kết nối DB riêng, các thread xuất phát cùng lúc nhờ `threading.Barrier`, rồi kiểm tra bất biến sau khi tất cả kết thúc. Test chạy trong **mọi PR**, vì mỗi worker của `pytest-xdist` đã có DB riêng.

Bắt buộc có các test:

| Kịch bản | Bất biến |
|---|---|
| N khách cùng Giữ hàng hoặc trừ Tồn kho cho K cái cuối cùng của một Biến thể (N > K) | Đúng K lần thành công, N − K lần ném `OUT_OF_STOCK`, Tồn kho không âm |
| N khách cùng dùng một Voucher còn K lượt | Đúng K lượt được dùng, không vượt `usage_limit` |
| Hai Đơn hàng cùng chứa 2 Biến thể nhưng thứ tự Dòng đơn hàng ngược nhau, cùng dùng một Voucher | Cả hai hoàn tất, không deadlock (khoá dòng Tồn kho theo thứ tự `variant_id`, rồi toàn bộ Biến thể theo id để kiểm tra snapshot, rồi mới khoá Voucher) |
| Hai yêu cầu hoàn khác key đồng thời trên một Payment, tổng vượt tiền thực nhận | Chỉ các yêu cầu trong hạn mức thành công; tổng requested + completed không vượt amount_received |
| Hai yêu cầu hoàn cùng payment_id và request_key | Chỉ một Refund được tạo, cả hai trả cùng refund_id; khác tham số bị từ chối |
| Checkout song song với đổi Giá bán hoặc thêm/sửa/xoá SalePrice | Writer và checkout đều khoá Variant; đơn dùng snapshot đã xác thực hoặc rollback PRICE_CHANGED, không lọt giá đọc trước khi writer commit |
| Hai checkout chứa nhiều Biến thể, availability chỉ đổi ở các Biến thể khác nhau | Khoá toàn bộ StockItem rồi toàn bộ Variant theo id trước khi đổi availability; không có thứ tự khoá một phần Variant trước phần còn lại |

### 2.3. Handler và outbox

- Mỗi handler: gọi 2 lần với cùng một sự kiện thì chỉ xử lý 1 lần (`ProcessedEvent`).
- Consumer ([07-async-events-jobs.md](./07-async-events-jobs.md) mục 1.3), test bằng handler giả: khoá delivery; thành công commit tác động, ProcessedEvent và completed cùng nhau. RetryLater/exception rollback savepoint handler, lưu bộ đếm và lịch DB, không ghi ProcessedEvent; DomainError khác rollback savepoint nhưng ghi ProcessedEvent và rejected, không retry.
- Relay: tạo từng cặp event–handler và marker deliveries_created_at nguyên tử, không tạo trùng khi hai relay cùng chạy. Relay không phụ thuộc Beat. Chết sau khi lưu hạn giao lại nhưng trước enqueue: sau hạn, delivery được giao tiếp.
- Redis đã nhận rồi mất task hoặc worker chết trước commit: relay giao lại delivery pending tới hạn; tác động cuối cùng chỉ commit một lần. Test task giao trùng chạy đồng thời trên PostgreSQL thật; consumer phải kiểm tra trạng thái và next_attempt_at.
- Handler hết retry: delivery failed và FailedEvent ghi cùng transaction; retry_failed_events mở lại đúng cặp, reset lịch/bộ đếm và ghi retried_at; không mở lại completed/rejected. Retry dùng lịch DB, mất task không làm reset số lỗi handler.
- Purge không xoá sự kiện có delivery pending/failed dù quá 90 ngày; chỉ xoá sự kiện đủ tuổi đã kết thúc mọi delivery. Replay không xoá dấu đã xử lý; thêm handler mới thì tạo delivery mới được.
- Email: handler commit EmailLog queued rồi process chết trước enqueue; job quét tìm lại và gửi được dù ProcessedEvent đã tồn tại. Mất task quét thì lần Beat tiếp theo vẫn phục hồi.
- Hai task cùng gửi một EmailLog: chỉ một task nhận lease; kết quả lease cũ không ghi đè lease mới. Nhà cung cấp nhận rồi worker chết trước lưu sent: cho phép gửi lại, không khẳng định chỉ gửi một email.
- Email queued lỗi theo backoff, sending hết lease được khôi phục; quá giới hạn chuyển failed và cảnh báo; retry_failed_emails chỉ mở lại failed được chọn. Email sent/cancelled không gửi lại. Email xác thực/reset không còn hợp lệ bị bỏ qua; không lưu token/link bí mật trong outbox hay EmailLog.
- customer-erased huỷ email chưa gửi, xoá người nhận và vô hiệu lease; worker đang giữ lease cũ không ghi đè kết quả sau đó.
- Job Celery Beat ([07-async-events-jobs.md](./07-async-events-jobs.md) mục 3.2): chạy 2 lần liên tiếp cho ra cùng kết quả.

Bắt buộc có các test handler sau:

| Kịch bản | Kỳ vọng |
|---|---|
| `payments.payment-succeeded` của khoản trả thêm tới khi đơn đã `PLACED`, hoặc tiền tới khi đơn đã `CANCELLED` (BR-PAY-05) | Đơn giữ nguyên; Hoàn tiền gắn đúng payment_id của sự kiện và key ổn định, không suy từ Mã đơn; gắn cờ unexpected_payment và phát sự kiện |
| Sự kiện thành công mới mang cùng payment_id đã dùng đưa đơn vào PLACED | Không tạo Hoàn tiền, không phát thêm OrderPlaced hay UnexpectedPaymentReceived |
| Một đơn có hai Thanh toán online cùng số tiền qua hai gateway | Lưu đúng payment_id dùng cho đơn; Hoàn tiền khoản trả thêm gắn đúng khoản và gateway, không hoàn nhầm khoản ban đầu |
| `payments.payment-failed` với `reason = amount_mismatch` (BR-PAY-04) | Tạo yêu cầu Hoàn tiền đúng `amount_received`; gắn cờ `payment_amount_mismatch`; đơn giữ `PENDING_PAYMENT` |
| `payments.refund-recorded` cho Hoàn tiền không gắn Đổi trả nào | Không Đổi trả nào đổi trạng thái |
| `ordering.order-cancelled` với `previous_status = PENDING_PAYMENT` (T4, T5) | notifications không gửi email (BR-NTF-01) |
| `shipping.shipment-created` tới khi đơn đã `CANCELLED` | Gọi `shipping.contracts.request_shipment_cancellation` (Vận đơn `cancel_requested`); gắn Cờ cần xử lý `shipment_after_cancel` |
| `shipping.shipment-delivered` tới khi đơn còn `PACKING` (T10 chưa chạy) | Ném `TransitionNotYetValid`; đơn giữ nguyên |
| `shipping.shipment-delivered` tới khi đơn đã `DELIVERED` hoặc `COMPLETED` | Không làm gì, không ném lỗi |
| `shipping.shipment-delivered` tới khi đơn đã `RETURNED_TO_SENDER` | Ném `InvalidTransition`; đơn giữ nguyên |
| `identity.email-verified` | Chỉ gắn các đơn có `contact_email` khớp (không phân biệt hoa thường) và chưa có `customer_id`; đơn đã thuộc Tài khoản khác không bị đổi |
| Đặt đơn online (T1) rồi IPN thành công (T3) | T1 không ghi sự kiện nào vào outbox; T3 ghi đúng một `ordering.order-placed` |

**Payload sự kiện không chứa secret hay PII** ([07-async-events-jobs.md](./07-async-events-jobs.md)): `backend/tests/test_event_payloads.py` duyệt mọi class `DomainEvent` đã đăng ký và fail nếu có field tên thuộc danh sách cấm (`email`, `phone`, `address`, `name`, `token`, `password`, `*_url`). Test này chỉ bắt lỗi theo tên field; reviewer vẫn phải đọc payload của mọi sự kiện mới. Test đặt ở `backend/tests/` (không thuộc `root_packages`) vì cần nhìn thấy sự kiện của mọi module.

**Hoàn tiền và audit:** test BR-REF-06 cho gọi lại cùng key/cùng tham số, key trùng khác tham số, vượt tiền thực nhận và hoàn tất lặp không phát thêm RefundRecorded. Callback IPN/đối soát trùng không cộng amount_received lần nữa. Tracker audit phải đúng danh sách [03 mục 10.1](./03-data-model.md#101-các-field-được-ghi-lịch-sử); ghi rồi redaction raw_payload không tạo bản sao PII trong history. Kiểm tra schema history không có field bị cấm, kể cả khi model được thêm field mới.

### 2.4. API

- **Phân quyền**: mỗi endpoint thử với Guest, Customer, Staff, Admin (theo cột quyền trong [04-api-contract.md](./04-api-contract.md)); Khách hàng này không xem được Đơn hàng của Khách hàng khác.
- **`X-Lookup-Token`**: `GET orders/{code}`, `POST orders/{code}/payments`, `POST orders/{code}/cancel` của Khách vãng lai bị từ chối khi thiếu token, token hết hạn hoặc token của đơn khác. Checkout của Khách vãng lai trả về `lookup_token` dùng được ngay cho ba endpoint này.
- **Lỗi**: đúng mã HTTP và đúng định dạng lỗi chuẩn (400, 401, 403, 404, 409, 429), gồm `409 PRICE_CHANGED` (có bảng tính mới trong `details`) và `409 SHIPMENT_IN_PROGRESS`.
- **`Idempotency-Key`**: thiếu key; gửi lại cùng key thì nhận lại đúng kết quả cũ; cùng key nhưng body khác thì ra `IDEMPOTENCY_CONFLICT`. Key lưu ở `shared_idempotency_key` (PostgreSQL), nên vẫn đúng khi Redis không chạy.
- **Còn xử lý:** hai request đồng thời cùng key chỉ có một operation_id/Payment; request còn lại nhận 202 PAYMENT_INITIALIZING. Khác body luôn 409, kể cả khi key in_progress. Purge không xoá key chưa rõ kết quả. Checkout commit kết quả key cùng Order, rollback không để Order mồ côi.
- **Phục hồi khởi tạo:** giả lập gateway đã tạo nhưng response timeout/process chết trước lưu; cùng key và job phục hồi phải giữ Payment, provider_txn_ref và provider_request_id. Query trước; chỉ retry create khi adapter có hợp đồng idempotency đã xác minh. Test fake provider đếm giao dịch ngoài DB để phát hiện tạo trùng; không chỉ đếm Payment.
- **Kết quả tới muộn:** IPN succeeded đến trước response tạo link; lưu response không hạ status/amount_received. Lease cũ không ghi đè lease mới. Quá hạn link không tạo/gia hạn link; gateway không cung cấp lại link thì API trả đang xử lý hoặc trạng thái cuối, không bịa redirect_url.
- **HTTP tích hợp ngoài transaction:** spy/mock transport xác nhận không có transaction atomic khi gọi gateway/GHN; lấy lại quote sau PRICE_CHANGED chỉ chạy sau rollback. Time-machine vượt lease rồi chạy job, không sleep trong test.
- **Throttle**: endpoint có throttle chặt (ví dụ `orders/lookup`) trả `429` khi vượt ngưỡng. Throttle theo `X-Client-IP` chỉ khi `X-BFF-Secret` đúng; thiếu hoặc sai secret thì bỏ qua `X-Client-IP` và throttle theo IP của kết nối ([ADR 0009](../adr/0009-nextjs-bff-django-private.md)).
- **Redis lỗi**: cache và throttle fail-open, request vẫn được xử lý ([10-nfr.md](./10-nfr.md) mục 2).
- **N+1 query**: `django-zeal` bật cho toàn bộ test; test fail nếu có N+1.

### 2.5. Bảo mật auth/JWT

Theo [05-auth-security.md](./05-auth-security.md) mục 9 và [ADR 0002](../adr/0002-auth-nextauth-session-django-jwt.md): sai thuật toán, `alg: none`, sai `aud`, hết hạn, sai `kid`, dùng lại refresh token (phải thu hồi cả chuỗi), đổi `token_version`, thu hồi qua `jti`, token storefront không dùng được cho back-office.

Thêm hai kịch bản về Tài khoản:

- **Đăng nhập Google vào Tài khoản chưa xác thực email** (chiếm tài khoản trước): Tài khoản được đánh dấu đã xác thực, mật khẩu cũ không còn đăng nhập được, mọi refresh token cũ bị thu hồi và access token cũ sai `tv`.
- **Một email một Tài khoản**: đăng ký Khách hàng bằng email của một Tài khoản Staff bị từ chối; đăng nhập storefront bằng Tài khoản Staff (mật khẩu hoặc Google) bị từ chối với lỗi chung.
- **Một successor:** hai request đồng thời dùng R1 chỉ tạo R2 một lần. R1.used_at, successor_jti và ciphertext response commit cùng transaction. Mất response rồi retry trong 10 giây nhận đúng cặp cũ, không gia hạn replay; Redis tắt vẫn không tạo nhánh mới.
- **Replay sau thu hồi:** logout/reset/Google takeover/ẩn danh/vô hiệu hoá giữa hai request → không trả lại token từ ciphertext. Kiểm tra trực tiếp account/tv/family từ DB dưới thứ tự khoá Account → Token; ciphertext liên quan được vô hiệu/xoá.
- **R2 đã dùng:** R1 lặp trong cửa sổ trả REFRESH_SUPERSEDED, không thu hồi nhầm family hoặc trả token cũ. R1 lặp ngoài cửa sổ thu hồi family. Mất ciphertext hoặc thiếu key không được cấp successor thay thế.
- **Mã hoá:** key khác, AAD sai, ciphertext bị sửa đều không decrypt được. Endpoint từ chối replay hết hạn dù job purge chưa chạy; purge/revoke xoá ciphertext. BFF multi-replica single-flight không dựa vào bộ nhớ một process; response cũ không ghi đè cặp mới hơn.
- **Redirect:** body gửi return_url bị từ chối; Host/Forwarded/Origin giả không đổi callback server dựng. Production chỉ HTTPS origin/path cố định; local có origin riêng. redirect_url giả host, userinfo, scheme lạ hoặc host giống tiền tố bị chặn. Return page không xác nhận thanh toán từ query string. Cấu hình origin đổi giữa các retry không làm đổi URL trong creation_input đã lưu.

### 2.6. Adapter nhà cung cấp

- **Chữ ký VNPay (HMAC-SHA512) và MoMo (HMAC-SHA256)**: unit test với dữ liệu mẫu lấy từ tài liệu của nhà cung cấp, gồm chữ ký đúng, sai một ký tự, thiếu field. Fake Gateway không kiểm tra chữ ký nên test này là nơi duy nhất bảo vệ phần đó.
- **Gọi HTTP** bằng respx: timeout, lỗi 5xx, response sai định dạng; GHN báo giá lỗi dùng fallback; chỉ phát shipment-creation-failed khi xác nhận bị từ chối/chưa tạo. Timeout tạo là creation_unknown và được đối soát; test cancel_shipment riêng.
- **Tạo Vận đơn mất response:** FakeShippingProvider đếm Vận đơn bên ngoài DB. Query theo shop/client code tìm lại cùng Vận đơn; hai task claim cùng lease không gọi tạo song song; stale result không ghi đè lease mới hoặc trạng thái vận chuyển xa hơn. ShipmentCreatedV1 chỉ ghi một lần kể cả webhook/query phát hiện trước response tạo.
- **Chưa rõ kết quả:** query timeout/not_found chưa chắc chắn giữ unknown, không đổi reference/payload và không tạo lại mù. Staff huỷ/bàn giao lại bị chặn. Sandbox phải kiểm tra trùng client code và độ trễ truy vấn trước khi bật retry tạo tự động; lỗi mạng hết retry không chuyển failed.
- **Cache phí:** cùng request chuẩn hoá thì hit; đổi shop/nơi gửi, service, địa chỉ đã mapping, cân nặng/kích thước, giá trị khai báo/COD hoặc revision thì miss. Hai cân nặng cùng bucket cũ không tự dùng chung phí. Fallback không lấp cache GHN thật; GHN phục hồi thì request sau lấy được phí thật. Không có secret hay PII liên hệ trong cache key/log.
- **IPN và webhook**: gọi trùng, sai chữ ký, sai số tiền, đến muộn sau khi đơn đã bị huỷ.

### 2.7. Flow xuyên module

Flow test gọi qua **HTTP** (`api_client`, `staff_client`, endpoint IPN của Fake Gateway), để đi qua đúng auth, `X-Lookup-Token`, `Idempotency-Key` và serializer như thực tế. Các bước do Celery Beat kích hoạt thì dùng `time-machine` để vượt mốc thời gian, rồi gọi thẳng task (ví dụ `ordering.cancel_expired_pending_orders`, `ordering.complete_delivered_orders`). Đánh dấu bằng `@pytest.mark.flow`.

Sau mỗi bước HTTP, flow test gọi `drain_events()` trong `shared/testing/events.py`. Hàm chạy các callback `on_commit` đang chờ, relay rồi handler (Celery chạy đồng bộ), và lặp tới khi không còn delivery tới hạn. Không chờ retry tương lai; test retry dùng time-machine tiến tới hạn rồi drain tiếp. Ví dụ sau IPN thành công, nó đưa `payments.payment-succeeded` tới handler của `ordering` để chạy T3; sau khi bàn giao, nó chạy task tạo Vận đơn và đưa `shipping.shipment-created` tới T10. Test riêng về mất task và worker dùng các điểm dừng/mô phỏng lỗi, không dựa vào eager mode để chứng minh broker bền vững.

Bắt buộc có 6 flow:

| Flow | Nội dung |
|---|---|
| `test_cod_checkout_flow.py` | Checkout COD → Thanh toán COD `pending` → bàn giao, Vận đơn được tạo → Đã giao, Thanh toán COD `succeeded` → Hoàn tất sau 7 ngày |
| `test_online_payment_success_flow.py` | Checkout online → Giữ hàng 15 phút, link thanh toán hết hạn sau 10 phút → IPN thành công → trừ Tồn kho, ghi `ordering.order-placed` → giao → Hoàn tất |
| `test_online_payment_failure_flow.py` | IPN thất bại, hoặc không ai trả tiền và Giữ hàng hết hạn sau 15 phút → đơn huỷ, Số lượng bán được và lượt Voucher được trả lại |
| `test_cancel_paid_order_flow.py` | Huỷ Đơn hàng đã thanh toán online → Hoàn tiền về đúng Cổng thanh toán đã nhận tiền |
| `test_returned_to_sender_flow.py` | Giao thất bại → Hoàn hàng → Staff xác nhận hàng về Kho → nhập lại Tồn kho; với đơn COD, Thanh toán COD chuyển `cancelled` |
| `test_return_refund_flow.py` | Đổi trả một phần được chấp nhận theo từng dòng (BR-RET-08) → Hoàn tiền đúng số tiền theo BR-RET-07 → Đổi trả chuyển `refunded` khi có `payments.refund-recorded`; Đơn hàng chỉ Hoàn tất khi không còn Đổi trả nào mở |

## 3. Marker của pytest

Khai báo trong `pyproject.toml` (`--strict-markers`):

| Marker | Ý nghĩa | Dùng để |
|---|---|---|
| `br("BR-XXX-NN", ...)` | Test kiểm tra một hay nhiều business rule | Lọc test theo quy tắc; `make br-report` |
| `concurrency` | Test chạy nhiều thread, cần `transaction=True` | `pytest -m concurrency` |
| `flow` | Flow xuyên module | `pytest -m flow` |

`make br-report` liệt kê các mã `BR-xxx` trong `04-business-rules.md` chưa có test nào gắn marker `br`. Lệnh này chỉ để xem, **không** chặn CI, vì nhiều quy tắc chưa có code.

## 4. Dữ liệu test và ranh giới module

Khi bootstrap, kiểm tra cấu hình import-linter bằng các package mẫu tạm: import contracts đúng chiều qua; service import model module khác fail; FK giữa model đúng chiều qua; import cùng lớp hoặc ngược chiều fail. Generator phải liệt kê đủ phần nội bộ thực sự tồn tại và bắt cấu hình cũ trong CI. Không coi việc lint-imports chạy qua trên package rỗng là đã chứng minh ranh giới.

- Dữ liệu test tạo bằng `factory-boy`, không dùng fixture JSON.
- Fixture không cần nghiệp vụ (ví dụ `api_client`) ở `shared/testing/fixtures.py`. Fixture phải tạo Tài khoản (`customer_client`, `staff_client`, `admin_client`) ở `backend/conftest.py`, vì `shared` không được import `modules.identity`.
- Mỗi module để factory ở `modules/<module>/tests/factories.py`.
- Test trong một module chỉ dùng factory của chính module đó và của các module lớp dưới, theo đúng chiều phụ thuộc trong [02-backend-structure.md](./02-backend-structure.md) mục 4. Ví dụ test của `ordering` dùng được factory của `catalog` và `inventory`; test của `inventory` không dùng được factory của `ordering`.
- `backend/tests/flows/` được dùng factory của mọi module.
- Contract `layers` của `import-linter` đã giữ quy tắc này, không cần contract riêng: test của `inventory` import factory của `ordering` là import ngược lớp. `backend/tests/` không thuộc `root_packages` nên không bị kiểm tra.
- Muốn kiểm tra dữ liệu của module khác (ví dụ Tồn kho sau khi đặt Đơn hàng), test gọi `contracts` của module đó, **không** import `models`, `services`, `selectors` của module đó. Test tuân theo cùng ranh giới như code thật ([02-backend-structure.md](./02-backend-structure.md) mục 8).

## 5. Hợp đồng API với frontend (OpenAPI)

- Schema được commit tại `backend/openapi.yaml`, sinh bằng `manage.py spectacular --validate --file openapi.yaml`. Frontend sinh TS client từ file này.
- CI sinh lại schema và fail nếu khác file đã commit. Vì vậy mọi thay đổi API đều hiện trong diff của PR.
- Chưa dùng công cụ phát hiện breaking change (`oasdiff`). Reviewer tự đọc diff của `openapi.yaml`; diff có xoá field hay endpoint thì PR phải nêu rõ và báo cho frontend.

## 6. Migration

- Migration chỉ đổi schema: không cần test; `makemigrations --check` và kiểm tra xung đột migration trong từng app ở CI là đủ. Hai app có cùng số migration là hợp lệ.
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
| `pytest` | Toàn bộ test qua, kể cả `concurrency` và `flow`. Chạy `pytest -n auto --cov=modules --cov-report=` (`pytest-cov` gom coverage từ các worker của `pytest-xdist`) |
| Coverage | ≥ 80% **branch coverage** (`[tool.coverage.run] branch = true`) cho `services/` và `handlers.py`, tính **riêng từng module**: mỗi module chạy `coverage report --include="modules/<module>/services/*,modules/<module>/handlers.py" --fail-under=80`; module chưa có cả hai thì bỏ qua. **Không** đặt ngưỡng cho toàn repo, để không ai phải viết test chỉ để lấp số |
| Migration | `makemigrations --check`, không có nhánh migration xung đột trong cùng app; số migration được lặp giữa các app |
| OpenAPI | Schema sinh ra trùng với `backend/openapi.yaml` |
| `pip-audit` | Không có lỗ hổng |

## 9. Chưa làm ở MVP

| Việc | Khi nào làm |
|---|---|
| Test tải theo [10-nfr.md](./10-nfr.md) mục 1 (p95 300/800 ms, 50 request/giây khi khuyến mãi), chạy bằng k6 trên staging | Trước đợt khuyến mãi lớn đầu tiên |
| `oasdiff` phát hiện breaking change của OpenAPI | Khi API có client ngoài frontend của team (ví dụ mobile app) |
| E2E qua trình duyệt | Thuộc repo frontend |

Ở MVP, hiệu năng chỉ được bảo vệ bằng `django-zeal` (N+1 query) và test concurrency (mục 2.2).
