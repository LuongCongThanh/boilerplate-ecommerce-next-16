# 07. Sự kiện và job chạy nền

> Trạng thái: **Bản nháp chờ review**. Quyết định nền tảng: [ADR 0007](../adr/0007-events-outbox-celery-no-kafka.md), [ADR 0003](../adr/0003-postgres-redis-celery.md).

## 1. Luồng sự kiện (Transactional Outbox)

```mermaid
sequenceDiagram
    participant S as Service (ví dụ checkout)
    participant DB as PostgreSQL
    participant RL as Outbox relay
    participant RD as Redis (Celery broker)
    participant W as Celery worker
    participant H as Handler (ví dụ notifications)

    S->>DB: BEGIN
    S->>DB: INSERT order …
    S->>DB: INSERT shared_outbox_event (OrderPlacedV1)
    S->>DB: COMMIT
    loop mỗi 1 giây
        RL->>DB: Tạo EventDelivery cho từng handler của outbox chưa lập danh sách, cùng transaction
        RL->>DB: Chọn delivery pending tới hạn, FOR UPDATE SKIP LOCKED; đặt hạn giao lại rồi COMMIT
        RL->>RD: dispatch_event(event_id, handler)
    end
    RD->>W: dispatch_event
    W->>DB: BEGIN; khoá EventDelivery; bỏ qua nếu đã kết thúc hoặc chưa tới hạn retry
    W->>H: Gọi handler trong savepoint của cùng transaction
    W->>DB: Ghi ProcessedEvent + delivery completed cùng tác động handler; COMMIT
```

### 1.1. Bảo đảm

| Bảo đảm | Có được nhờ |
|---|---|
| Sự kiện được lưu bền vững | Sự kiện ghi cùng transaction với dữ liệu nghiệp vụ trong PostgreSQL |
| Tự giao lại khi mất task hoặc worker chết | `EventDelivery` lưu từng cặp sự kiện–handler; relay quét lại các delivery chưa kết thúc tới hạn |
| Không lặp tác động DB của cùng cặp sự kiện–handler | Khoá delivery và ghi `shared_processed_event` cùng transaction với tác động của handler |
| Một handler lỗi không ảnh hưởng handler khác | Mỗi cặp (sự kiện, handler) là một Celery task riêng |
| Có thể phát lại | Bảng outbox giữ sự kiện **90 ngày** **[Giả định]**; lệnh `manage.py replay_events --type … --since …` |

### 1.1.1. PostgreSQL quyết định công việc còn chờ

- `publish()` chỉ ghi `OutboxEvent`. Relay lập danh sách handler theo `event_type` và `schema_version`, tạo `EventDelivery` với `UNIQUE(event_id, handler)` rồi ghi `deliveries_created_at` trong cùng transaction. Marker này chỉ có nghĩa đã lập danh sách, không có nghĩa handler đã chạy. Không có handler thì ghi marker và log để tránh quét mãi.
- Relay chạy độc lập với Celery Beat, quét mỗi giây. Với delivery `pending` có cả `next_attempt_at` và `next_dispatch_at` tới hạn, relay khoá dòng bằng `select_for_update(skip_locked=True)`, đặt `next_dispatch_at = now + 3 phút` **[Giả định]**, commit rồi mới enqueue. Không giữ transaction DB khi gọi broker. Chết trước enqueue, Redis mất task hay worker chết trước commit đều khiến delivery được giao lại sau hạn này.
- Consumer khoá dòng delivery trong toàn transaction xử lý; kiểm tra trạng thái và `next_attempt_at` trước khi gọi handler. Task trùng chờ khoá rồi thấy kết quả đã commit thì kết thúc. Hạn giao lại dài hơn `task_time_limit` 120 giây; timeout không cho phép bỏ qua khoá DB. Task tới muộn vẫn phải kiểm tra trạng thái hiện tại.
- `ProcessedEvent` và trạng thái delivery `completed`/`rejected` được ghi cùng transaction với kết quả xử lý. Retry dùng `attempts`, `next_attempt_at` trong PostgreSQL; không dùng bộ đếm Celery làm nguồn quyết định. `last_dispatched_at` chỉ phục vụ quan sát. Broker không hoạt động thì relay giữ công việc trong DB và thử tiếp, không tính là handler thất bại.
- Chỉ purge sự kiện quá 90 ngày đã có `deliveries_created_at` và mọi delivery đã `completed` hoặc `rejected`, cùng delivery, ProcessedEvent và FailedEvent liên quan; giữ cả sự kiện và delivery `pending`/`failed` cho tới khi được xử lý. Cảnh báo công việc tồn đọng; không âm thầm xoá khi hết thời gian lưu thông thường.
- API công khai `shared.events.get_delivery_outcomes(event_id, handler_names)` trả trạng thái từng handler được yêu cầu: missing/pending/completed/rejected/failed. Không suy thành công từ danh sách rỗng. Ẩn danh dùng required_handlers đã chốt trên ErasureRequest; replay không tự mở rộng yêu cầu đã hoàn tất.
- `replay_events` bảo đảm delivery tồn tại cho handler được chọn, có thể thêm handler mới vào sự kiện cũ; không xoá dấu đã xử lý hay chạy lại cặp đã hoàn tất. Cặp `failed` cần lệnh `retry_failed_events` để mở lại có chủ đích.

### 1.2. Không bảo đảm

**Thứ tự.** Handler không tự kiểm tra thứ tự. Với Đơn hàng, các transition do sự kiện kích hoạt tự đối chiếu trạng thái hiện tại ([02-backend-structure.md](./02-backend-structure.md) mục 7.7, [05-order-lifecycle.md](../business/05-order-lifecycle.md) mục 4.2): sự kiện cho bước đơn đã qua thì không làm gì, sự kiện tới sớm thì báo consumer thử lại sau, sự kiện mâu thuẫn với trạng thái đơn thì bị từ chối.

**Gửi ra hệ thống ngoài đúng một lần.** Chống trùng bằng transaction chỉ bao phủ tác động trong PostgreSQL. Email hoặc request nhà cung cấp phải chạy ngoài transaction và có cơ chế khôi phục riêng; email vẫn có thể trùng khi nhà cung cấp đã nhận nhưng worker chết trước lúc lưu `sent`. Việc tự khôi phục đòi hỏi PostgreSQL và relay/worker hoạt động trở lại; delivery `failed` cần người vận hành xử lý.

### 1.3. Retry và lỗi

Handler báo kết quả cho consumer bằng cách kết thúc bình thường hoặc ném exception. Consumer quyết định theo bảng sau, nên tác giả handler không phải tự bắt lỗi:

| Handler kết thúc bằng | Consumer làm gì |
|---|---|
| Chạy xong | Commit tác động handler, `ProcessedEvent` và delivery `completed` |
| `RetryLater`, ví dụ `TransitionNotYetValid` | Rollback savepoint handler; không ghi `ProcessedEvent`; tăng bộ đếm và lưu lịch retry trên delivery trong transaction ngoài |
| `DomainError` khác, ví dụ `InvalidTransition` | Rollback savepoint handler nhưng ghi `ProcessedEvent` và delivery `rejected`, không retry. Log `WARNING` `event_rejected` kèm `event_type`, `handler`, `code` |
| Exception khác | Rollback savepoint handler; lưu retry như `RetryLater`. Nếu kết nối DB hỏng, toàn transaction rollback; relay giao lại theo hạn đã lưu |

- Lịch retry lưu trong DB: sau lần đầu, thử lại tối đa **5 lần**, chờ lần lượt 10 giây, 1 phút, 5 phút, 15 phút, 30 phút **[Giả định]**. `attempts` đếm lỗi handler đã lưu được; task bị mất không tiêu hao lượt retry. Mỗi lỗi đặt lại cả `next_attempt_at` và `next_dispatch_at` theo lịch này.
- Hết số lần retry: chuyển delivery `failed`, ghi `FailedEvent` (`event_id`, `handler`, `error`, `failed_at`) cùng transaction, gửi cảnh báo Sentry. Áp dụng cả cho `RetryLater`. `manage.py retry_failed_events` khoá delivery `failed`, đặt lại `pending`, bộ đếm và lịch về hiện tại, ghi `retried_at`; relay giao lại. Không tự mở lại delivery `completed`/`rejected`.
- Relay lỗi kết nối Redis: sự kiện vẫn nằm trong outbox, relay tự thử lại.
- `enqueue_on_commit` cho công việc có bản ghi DB bắt lỗi kết nối/enqueue broker, ghi log và cảnh báo mà không biến request đã commit thành lỗi API. Không xoá hay đánh dấu hoàn tất khi enqueue thất bại; relay/job quét sẽ khôi phục. Lỗi lập trình hoặc dữ liệu không được âm thầm bỏ qua.

## 2. Danh mục sự kiện

Tên theo dạng `<module>.<event>`, có `schema_version`. Class nằm trong `events.py` của module phát.

**Payload không chứa secret hay PII.** Payload chỉ mang ID, Mã đơn, số tiền và mã trạng thái. Handler cần dữ liệu nhạy cảm thì hỏi `contracts` của module sở hữu ngay lúc xử lý, ví dụ `identity.contracts.issue_password_reset_link(account_id)`. Lý do: outbox giữ sự kiện 90 ngày, có thể bị phát lại, và nằm trong mọi bản backup; token hay số điện thoại để ở đây sẽ sống lâu hơn và lộ rộng hơn bản gốc.

| Sự kiện | Phát bởi | Dữ liệu chính | Handler |
|---|---|---|---|
| `identity.customer-registered` v1 | identity | `account_id`, `language` | notifications: tạo EmailLog xác thực; task cấp link và gửi ngoài transaction |
| `identity.email-verified` v1 | identity | `account_id` | Phát mỗi khi email chuyển sang đã xác thực, kể cả qua đăng nhập Google. ordering: gắn các Đơn hàng có `contact_email` khớp (không phân biệt hoa thường) và `customer_id` null vào Tài khoản (BR-ORD-08) |
| `identity.password-reset-requested` v1 | identity | `account_id` | notifications: tạo EmailLog reset; task cấp link và gửi ngoài transaction |
| `identity.customer-erased` v1 | identity | `erasure_request_id` | ordering: ẩn danh Đơn hàng, xoá Giỏ hàng, gọi `shipping.contracts.redact_provider_payloads` và `payments.contracts.redact_provider_payloads` theo `reference`; promotions: ẩn danh `phone` trong lượt dùng Voucher; notifications: ẩn danh `to_address`. Mọi handler lấy đối tượng cần ẩn danh qua `identity.contracts.get_erasure_subject` |
| `ordering.order-placed` v1 | ordering | `order_code`, `payment_method`, `total` | Phát khi đơn **vào** `PLACED` (T2, T3). notifications: COD gửi "Đặt đơn thành công", online gửi "Thanh toán thành công" |
| `ordering.order-cancelled` v1 | ordering | `order_code`, `reason`, `refund_required`, `previous_status` | notifications: email "Đơn đã huỷ", trừ khi `previous_status = PENDING_PAYMENT` (T4, T5: BR-NTF-01) |
| `ordering.unexpected-payment-received` v1 | ordering | `order_code`, `amount` | Phát cùng lúc gắn cờ `unexpected_payment` (BR-PAY-05). notifications: email báo tiền sẽ được hoàn; với đơn đã huỷ thì báo thêm đơn đã hết hạn ([05](../business/05-order-lifecycle.md) mục 4.1) |
| `ordering.order-shipped` v1 | ordering | `order_code`, `tracking_code` | notifications: email "Đang giao" |
| `ordering.order-delivered` v1 | ordering | `order_code` | notifications: email "Đã giao" |
| `payments.payment-succeeded` v1 | payments | `reference`, `payment_id`, `amount`, `gateway` | Chỉ phát cho Thanh toán online. ordering: T3, lưu payment_id dưới khoá Order. Cùng payment_id đã dùng cho đơn thì bỏ qua; khoản trả thêm hoặc tiền tới sau huỷ: request_refund với payment_id từ sự kiện và request_key ổn định, gắn cờ unexpected_payment và phát ordering.unexpected-payment-received (BR-PAY-05) |
| `payments.payment-failed` v1 | payments | `reference`, `payment_id`, `reason`, `amount_received` | ordering: ghi nhận, cho phép thử lại; `reason = amount_mismatch` thì request_refund với payment_id từ sự kiện, amount_received và key ổn định và gắn cờ `payment_amount_mismatch` (BR-PAY-04) |
| `payments.refund-recorded` v1 | payments | `reference`, `refund_id`, `amount` | notifications: email "Đã hoàn tiền"; ordering: chuyển Đổi trả có `refund_id` khớp sang `refunded`, không khớp thì bỏ qua |
| `shipping.shipment-created` v1 | shipping | `reference`, `provider_order_code` | ordering: T10, gọi `inventory.contracts.dispatch_stock` để xoá Hàng chờ xuất. Nếu đơn đã `CANCELLED`: gọi `shipping.contracts.request_shipment_cancellation` và gắn cờ `shipment_after_cancel` |
| `shipping.shipment-creation-failed` v1 | shipping | `reference`, `reason` | ordering: gắn cờ `shipment_failed`, đơn giữ `PACKING` |
| `shipping.shipment-delivered` v1 | shipping | `reference`, `delivered_at` | ordering: T11 |
| `shipping.shipment-returned` v1 | shipping | `reference` | ordering: T12 |

T1 (đơn online vào `PENDING_PAYMENT`) không phát sự kiện nào; Người mua chỉ nhận email khi thanh toán thành công. Không còn sự kiện `ordering.order-paid`: `order-placed` của đơn online đã mang ý nghĩa này.

Thanh toán COD (`start_cod_payment`, `record_cod_collected`, `cancel_cod_payment`) **không** phát sự kiện, vì `ordering` là bên gọi nên đã biết kết quả. Nếu `record_cod_collected` phát `payments.payment-succeeded`, handler của `ordering` sẽ thấy đơn `DELIVERED` không ở `PENDING_PAYMENT` và tạo Hoàn tiền nhầm theo BR-PAY-05.

## 3. Celery

### 3.1. Queue

| Queue | Dùng cho | Worker |
|---|---|---|
| `default` | Job theo lịch | Chung |
| `events` | `dispatch_event` | Chung |
| `emails` | Gửi email | Chung; tách riêng khi tải lớn |
| `integrations` | Gọi API VNPay, MoMo, GHN: Đối soát, tạo và huỷ Vận đơn (tạo và huỷ Vận đơn luôn chạy nền, xem [06-integrations.md](./06-integrations.md) mục 4) | Chung; giới hạn số chạy đồng thời để không vượt rate limit của nhà cung cấp |

Code nghiệp vụ đẩy task bằng `shared.tasks.enqueue_on_commit`, không gọi `.delay()` trực tiếp ([02-backend-structure.md](./02-backend-structure.md) mục 9.1).

### 3.2. Lịch job (Celery Beat, lưu bằng `django-celery-beat`)

| Job | Tần suất | Module | Liên quan |
|---|---|---|---|
| `ordering.cancel_expired_pending_orders` | Mỗi phút | ordering | T4 |
| `payments.reconcile_pending_payments` | Mỗi 5 phút | payments | T3, ADR 0005; Payment quá hạn link mà chưa thanh toán thì chuyển `expired` |
| `shipping.reconcile_shipments` | Mỗi 15 phút | shipping | T11, T12; query mã shop cho requested/creation_unknown hết lease, không retry create mù; thử huỷ lại cancel_requested quá 15 phút |
| `ordering.complete_delivered_orders` | Mỗi giờ | ordering | T13 |
| `ordering.compute_best_sellers` | Mỗi ngày 02:00 | ordering | BR-CAT-12; ghi kết quả vào `catalog` qua `catalog.contracts.set_best_seller_counts` |
| `ordering.purge_expired_guest_carts` | Mỗi ngày 03:00 | ordering | BR-CRT-02 |
| `notifications.recover_pending_emails` | Mỗi phút **[Giả định]** | notifications | Đẩy lại EmailLog `queued` tới hạn hoặc `sending` hết lease; xem mục 4 |
| `shared.purge_old_outbox_events` | Mỗi ngày 03:30 | shared | Chỉ xoá sự kiện quá 90 ngày đã hoàn tất mọi delivery; xoá delivery và ProcessedEvent tương ứng |
| `shared.purge_idempotency_keys` | Mỗi ngày 03:45 | shared | Chỉ xoá key completed quá 24 giờ; giữ in_progress chưa rõ kết quả |
| `identity.purge_refresh_replays` | Mỗi phút **[Giả định]** | identity | Xoá ciphertext replay hết hạn; endpoint vẫn kiểm tra hạn và thu hồi trước decrypt, không chờ job |
| `identity.purge_expired_tokens` | Mỗi ngày 04:00 | identity | Refresh token, reset token hết hạn |
| `identity.reconcile_erasure_requests` | Mỗi phút **[Giả định]** | identity | Chỉ hoàn tất processing khi mọi handler bắt buộc completed; thiếu/failed/rejected thì giữ trạng thái và cảnh báo |
| `payments.recover_payment_initializations` | Mỗi phút **[Giả định]** | payments | Khôi phục prepared/unknown hết lease bằng cùng Payment và mã nhà cung cấp; không ghi đè IPN (06 mục 3.1) |

Mọi job đều **idempotent** và xử lý theo lô (ví dụ 200 đơn mỗi lần) để chạy lại an toàn.

### 3.3. Cấu hình quan trọng

| Thiết lập | Giá trị | Lý do |
|---|---|---|
| `task_acks_late` | `True` | Worker chết giữa chừng thì task được giao lại |
| `task_reject_on_worker_lost` | `True` | Như trên |
| `worker_prefetch_multiplier` | `1` | Không giữ nhiều task trong một worker |
| `task_time_limit` | 120 giây | Chặn task treo |
| `CELERY_TASK_ALWAYS_EAGER` | `True` chỉ trong `settings/test.py` | Test chạy đồng bộ |
| Kết quả task | Không lưu (`task_ignore_result = True`) | Không cần result backend |
| Redis `maxmemory-policy` | `noeviction` | Redis vừa là broker vừa là cache; nếu Redis tự đẩy key ra khi đầy thì có thể mất task. Vì vậy mọi key cache phải có TTL |

Các cấu hình ack hỗ trợ giao lại task nhưng không thay thế trạng thái công việc trong PostgreSQL; tác vụ vẫn phải chạy lại an toàn. Tham khảo [tài liệu Celery về task và acks_late](https://docs.celeryq.dev/en/stable/userguide/tasks.html).

## 4. Email: hàng đợi bền vững trong PostgreSQL

- Handler gọi service tạo `EmailLog(status="queued")` cùng transaction với `ProcessedEvent`, `UNIQUE(event_id, template)`; lưu ID nguồn (`account_id`, `order_code` hoặc `refund_id`) để dựng lại nội dung. `context` chỉ cho phép snapshot `amount`, `currency` từ sự kiện nếu template cần số tiền của đúng lần phát sinh, không phụ thuộc outbox còn giữ hay không. Không lưu token, link bí mật, raw payload hay HTML chứa PII trong hàng đợi. Sau commit chỉ enqueue `send_email(email_log_id)` để giảm độ trễ; DB là nguồn công việc còn chờ.
- Task mở transaction ngắn để khoá EmailLog, bỏ qua `sent`/`failed`/`cancelled`, `queued` chưa tới `next_attempt_at` hoặc `sending` có lease chưa hết; nhận lease bằng `lease_token` mới, `lease_expires_at = now + 3 phút` **[Giả định]**, đặt `sending` và tăng `attempts`. Sau commit mới lấy dữ liệu qua contracts, cấp token xác thực/reset nếu cần, render và gửi email ngoài transaction. Link bí mật chỉ tồn tại trong bộ nhớ lúc gửi.
- Ghi kết quả trong transaction ngắn, chỉ khi `lease_token` còn khớp. Thành công → `sent`; lỗi → `queued` với `next_attempt_at` theo lịch 10 giây, 1 phút, 5 phút, 15 phút, 30 phút; sau lần gửi thứ 6 thất bại → `failed` và cảnh báo Sentry. Claim sau lease hết hạn vẫn tính một lần gửi để giới hạn các lần worker chết; quá giới hạn chuyển `failed` để kiểm tra thủ công. Timeout gửi phải ngắn hơn lease và task time limit.
- `recover_pending_emails` quét `queued` tới hạn và `sending` hết lease để đẩy lại task. Nếu task quét hoặc task gửi mất trong Redis, lần quét tiếp theo vẫn tìm thấy công việc. Không cần phát lại sự kiện đã xử lý. Lệnh `manage.py retry_failed_emails` mở lại các email `failed` được chọn, đặt lại bộ đếm, ghi log thao tác; không mở lại email `sent`/`cancelled`.
- Nhà cung cấp đã nhận nhưng chưa lưu `sent` thì lần khôi phục có thể gửi trùng; `UNIQUE(event_id, template)` chỉ chống tạo hai EmailLog. Dùng Message-ID ổn định theo EmailLog để tra cứu, không coi đây là bảo đảm nhà cung cấp chống trùng.
- Trước khi gửi, kiểm tra nguồn còn hợp lệ: chuyển `cancelled` (chỉ khi lease còn khớp) cho email xác thực khi tài khoản đã xác thực, reset khi tài khoản không còn hoạt động hoặc nguồn không còn hợp lệ, và trường hợp không còn địa chỉ nhận; `customer-erased` chuyển email chưa gửi của đối tượng sang `cancelled`, xoá `to_address` và vô hiệu lease. Task lấy lại dữ liệu mới ngay trước khi gửi; việc gửi đã bắt đầu ở nhà cung cấp không thể thu hồi bằng transaction DB.
