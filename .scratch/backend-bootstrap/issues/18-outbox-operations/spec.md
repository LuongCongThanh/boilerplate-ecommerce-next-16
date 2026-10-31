# Lệnh vận hành và theo dõi outbox

Status: resolved

**PR:** #38

Blocked by: 10

Spec: [spec.md](../../spec.md)

Tách từ ticket [10](../10-shared-events-outbox/spec.md).

## Việc cần làm

Theo [07 mục 3](../../../../docs/architecture/07-async-events-jobs.md):

- `delivery_lag()`, `get_delivery_outcomes(event_id, handler_names)`.
- Job `purge_old_outbox_events`, đăng ký lịch trong `config/celery.py`.
- Lệnh `retry_failed_events` và `replay_events`.

## Quyết định

Chốt khi grilling ngày 30/10/2026.

| Chủ đề | Quyết định |
|---|---|
| Tài liệu chi phối | `shared/events/selectors.py`, `shared/events/__init__.py`: 07 §1.1.1 (`delivery_lag`, `get_delivery_outcomes`), 03 §10 (bên gọi ẩn danh), 02 §5 (API công khai của `shared/events`), §9.2. `shared/events/operations.py`, `shared/events/relay.py`, `shared/management/commands/retry_failed_events.py`, `replay_events.py`: 07 §1.1.1, §1.3, 03 §1.4 (ghi chú `retry_failed_events`), 02 §5, §9.1 (transaction trong command hạ tầng của `shared`), §9.6 (log). `shared/tasks.py`, `config/celery.py`: 07 §3.2 (lịch, idempotent, theo lô), 03 §1.4 (purge), 02 §5, §9.2 (tên Celery task). Test: 07 §5, 12 §2.3, 02 §9.2 (tên file test), §9.5 (factory, time-machine) |
| Không đổi schema | `retried_at` và partial index `failed_at WHERE status='failed'` đã có từ ticket 10; không thêm migration |
| `delivery_lag()` | Trả `timedelta`, `timedelta(0)` khi không tồn đọng. Lớn nhất giữa `now − occurred_at` của sự kiện chưa có `deliveries_created_at` và `now − next_attempt_at` của delivery `pending` có `next_attempt_at ≤ now`. Khác 07 §1.1.1: tài liệu ghi `created_at`, nhưng `OutboxEvent` không có cột này; `occurred_at` ghi cùng transaction và có partial index. Sửa 07 ở phase sync |
| `get_delivery_outcomes(event_id, handler_names)` | Trả `dict[str, DeliveryStatus \| None]` có đủ mọi tên được hỏi; `None` = chưa có delivery (missing). Chỉ truy vấn `shared_event_delivery` |
| Vị trí | `delivery_lag`, `get_delivery_outcomes` ở `shared/events/selectors.py` mới, export qua `shared/events/__init__.py`. Logic retry, replay, purge ở `shared/events/operations.py` mới; command và task là lớp mỏng gọi vào đó (ticket [26](../26-outbox-refactor-smells/spec.md) chuyển tiếp sang method của model). Cập nhật cây 02 §5 ở phase sync |
| `retry_failed_events` | Bộ lọc `--event-id`, `--handler`, `--type` kết hợp được, hoặc `--all`; không có bộ lọc nào → `CommandError`. Khoá bằng `select_for_update`, chỉ lấy dòng còn `failed`; đặt `pending`, `attempts = 0`, `next_attempt_at = next_dispatch_at = now`, `retried_at = now`. Giữ `failed_at`, `last_error` làm dấu vết (lần lỗi sau ghi đè). Không mở lại `completed`/`rejected`. Log `event_delivery_retried` từng cặp và một dòng tổng kèm số lượng. Thêm khi review (B2/B8, T4): `--handler` chưa đăng ký → `CommandError`; delivery có handler không còn trong registry thì không mở lại (mở lại sẽ kẹt `pending` mãi và đẩy `delivery_lag` lên), log `WARNING` `event_delivery_retry_skipped`; hàm trong `operations.py` tên `retry_failed_events`, trùng tên lệnh |
| `replay_events` | `--type` và `--since` (ISO datetime) bắt buộc; `--handler` tuỳ chọn, mặc định mọi handler đang đăng ký cho `(event_type, schema_version)` của từng sự kiện; tên handler không đăng ký, hoặc không đăng ký cho `--type` → `CommandError` (thêm khi review, B6). Sự kiện có `deliveries_created_at ≥ since`: tạo delivery còn thiếu (đổi khi review, B1: khoảng hở khi deploy là lúc relay cũ lập danh sách, không phải lúc sự kiện xảy ra; sự kiện phát ngay trước mốc deploy nhưng được lập danh sách sau mốc vẫn phải được phát lại). Mỗi lô khoá sự kiện bằng `select_for_update` để purge chạy đồng thời không xoá sự kiện giữa chừng; purge khoá theo thứ tự `id` như replay (thêm khi review, B4). Log ghi số sự kiện đã xét và số delivery tạo mới (thêm khi review, B6/T5) bằng `bulk_create(ignore_conflicts=True)`; delivery đã có giữ nguyên (kể cả `failed`, `completed`). Sự kiện chưa có marker: bỏ qua, relay sẽ lập danh sách. Lô 100 sự kiện, mỗi lô một transaction. Tách đoạn dựng delivery trong `relay.create_deliveries` thành helper `build_deliveries(event, handlers, now)` dùng chung |
| `purge_old_outbox_events` | Celery task trong `shared/tasks.py`, `name="shared.purge_old_outbox_events"`, queue `default`; `beat_schedule` trong `config/celery.py` key `shared.purge_old_outbox_events`, `crontab(hour=3, minute=30)` theo `CELERY_TIMEZONE`. Hằng `OUTBOX_RETENTION = 90 ngày` theo `occurred_at`. Chỉ xoá sự kiện đã có marker và không còn delivery `pending`/`failed` (sự kiện có marker mà không có delivery cũng xoá); delivery bị xoá theo `CASCADE`. Xoá theo lô 1.000, mỗi lô một transaction, tới khi hết. Còn sự kiện quá 90 ngày bị giữ → log `WARNING` `outbox_purge_kept_unfinished` kèm số lượng. Sentry Cron check-in: khi cấu hình Sentry |
| Test | `shared/events/tests/`: `test_selectors.py`, `test_retry_failed_events.py`, `test_replay_events.py`, `test_purge.py`; seam là `call_command(...)`, gọi task trực tiếp và hàm public. Dữ liệu bằng `OutboxEventFactory`, `EventDeliveryFactory`; thời gian cố định bằng `time-machine`, purge kiểm cả hai phía mốc 90 ngày |
| Mode | full: 4 AC (vượt ngưỡng lite) |

## Acceptance criteria

- [x] `retry_failed_events` mở lại delivery `failed` và lần chạy sau thành công.
- [x] Purge không xoá sự kiện còn delivery `pending` hoặc `failed`.
- [x] `get_delivery_outcomes` trả đúng trạng thái của từng handler được hỏi.
- [x] Các kịch bản ở [07 mục 5](../../../../docs/architecture/07-async-events-jobs.md#5-kịch-bản-kiểm-thử) về lệnh vận hành và purge đều có test.
