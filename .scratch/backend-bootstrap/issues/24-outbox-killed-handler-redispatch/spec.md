# Delivery bị kill do time limit được giao lại vô hạn

Status: resolved

**PR:** #47

Spec: [spec.md](../../spec.md)

Tách từ review của ticket [10](../10-shared-events-outbox/spec.md) ngày 30/10/2026 (finding B3).

## Bối cảnh

[07 mục 1.3](../../../../docs/architecture/07-async-events-jobs.md#13-retry-và-lỗi) quy định `attempts` chỉ đếm lỗi handler đã lưu được; task bị mất không tiêu lượt retry. Handler chạy quá `CELERY_TASK_TIME_LIMIT` (120 giây) hoặc làm worker hết bộ nhớ thì process bị kill trước khi consumer kịp lưu lỗi: transaction rollback, delivery giữ `pending` với `attempts` cũ, relay giao lại sau `REDISPATCH_AFTER` (3 phút), lại bị kill. Vòng này lặp vô hạn, không bao giờ chuyển `failed` nên không có cảnh báo Sentry (`event_delivery_failed`).

## Việc cần làm

- Chọn cách chặn: đếm số lần giao (`dispatch_count` hoặc dùng `last_dispatched_at`) và chuyển `failed` khi vượt ngưỡng, hoặc `soft_time_limit` để consumer bắt `SoftTimeLimitExceeded` và lưu như lỗi handler.
- Sửa 07 mục 1.3 và 03 mục 1.4 nếu thêm cột hoặc đổi quy tắc "task bị mất không tiêu lượt retry".

## Quyết định

Chốt khi grilling ngày 31/10/2026.

| Chủ đề | Quyết định |
|---|---|
| Tài liệu chi phối | `shared/events/models.py`, `shared/migrations/0005_*` → 03 §1.4, 02 §9.2, 12 §6. `shared/events/consumer.py` → 07 §1.1.1, §1.3, 02 §9.1 (transaction trong consumer). `shared/events/operations.py` (`retry_failed_events`) → 07 §1.3, 03 §1.4. Test `shared/events/tests/` → 12 §2.3, 02 §9.2, §9.5 |
| Cơ chế | Đếm lần chạy dở, không dùng `soft_time_limit` và không đếm số lần relay giao. Cột mới `EventDelivery.interrupted_runs` (`integer`, mặc định 0, `CHECK >= 0`): số lần liên tiếp handler đã bắt đầu chạy mà consumer không lưu được kết quả. Đếm lần relay giao thì task mất do Redis cũng bị tính (trái AC2); `soft_time_limit` không bắt được worker hết bộ nhớ |
| Consumer, hai transaction | Transaction 1 (ngắn): khoá delivery, kiểm `pending` và `next_attempt_at`, kiểm handler và class sự kiện còn đăng ký (thiếu thì giữ như cũ: log `event_handler_missing`, không tăng bộ đếm). `interrupted_runs` đã ≥ ngưỡng thì chuyển `failed` (không gọi handler); ngược lại tăng 1 rồi commit. Transaction 2: khoá lại, kiểm lại `pending` và `next_attempt_at`, chạy handler như cũ; mọi kết quả lưu được (`completed`, `rejected`, lịch retry, `failed` do hết retry) đặt `interrupted_runs = 0` cùng transaction. Worker bị kill hoặc kết nối DB hỏng giữa transaction 2 thì bộ đếm đã commit vẫn còn |
| Ngưỡng | `MAX_INTERRUPTED_RUNS = 3` lần liên tiếp; lần giao thứ 4 chuyển `failed`. Khoảng 10 phút với hạn giao lại 3 phút; hết bộ nhớ thì Celery giao lại ngay (`task_reject_on_worker_lost`) nên nhanh hơn |
| Khi chuyển `failed` | Ghi `failed_at`, `last_error = "HandlerInterrupted"` (cùng dạng tên class của `describe_error`), log `ERROR` `event_delivery_failed` kèm `interrupted_runs` để Sentry cảnh báo như khi hết retry |
| `attempts` | Không đổi ý nghĩa: chỉ đếm lỗi handler đã lưu được. Lần chạy dở đếm riêng ở `interrupted_runs` |
| `retry_failed_events` | Đặt `interrupted_runs = 0` cùng `attempts`, để delivery `failed` vì chạy dở được chạy lại thật |
| Task trùng | Task trùng tới giữa hai transaction có thể tăng bộ đếm thêm 1, nhưng transaction 2 của task đầu đặt về 0 khi lưu kết quả; task trùng sau đó thấy delivery đã kết thúc và bỏ qua |
| Rủi ro chấp nhận (review S2/B2) | Task trùng chen vào khe giữa transaction 1 và 2 đúng lúc bộ đếm vừa lên ngưỡng làm delivery `failed` sớm một lần. Khe rất ngắn, có cảnh báo `event_delivery_failed` và mở lại được bằng `retry_failed_events` |
| Rủi ro chấp nhận (review B3) | Gián đoạn không do handler (cold shutdown khi deploy, DB failover, worker hết bộ nhớ vì task khác) cũng tính là lần chạy dở. Cần 3 lần liên tiếp trên cùng delivery mới chuyển `failed` |

## Acceptance criteria

- [x] Handler luôn vượt time limit thì delivery cuối cùng chuyển `failed` và có log `ERROR`, không giao lại vô hạn.
- [x] Task mất do Redis (không phải do handler) vẫn không tiêu lượt retry.
