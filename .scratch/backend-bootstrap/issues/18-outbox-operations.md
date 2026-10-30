# Lệnh vận hành và theo dõi outbox

Status: ready-for-agent

Blocked by: 10

Spec: [spec.md](../spec.md)

Tách từ ticket [10](./10-shared-events-outbox.md).

## Việc cần làm

Theo [07 mục 3](../../../docs/architecture/07-async-events-jobs.md):

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
| Vị trí | `delivery_lag`, `get_delivery_outcomes` ở `shared/events/selectors.py` mới, export qua `shared/events/__init__.py`. Logic retry, replay, purge ở `shared/events/operations.py` mới; command và task là lớp mỏng gọi vào đó (ticket [26](./26-outbox-refactor-smells.md) chuyển tiếp sang method của model). Cập nhật cây 02 §5 ở phase sync |
| `retry_failed_events` | Bộ lọc `--event-id`, `--handler`, `--type` kết hợp được, hoặc `--all`; không có bộ lọc nào → `CommandError`. Khoá bằng `select_for_update`, chỉ lấy dòng còn `failed`; đặt `pending`, `attempts = 0`, `next_attempt_at = next_dispatch_at = now`, `retried_at = now`. Giữ `failed_at`, `last_error` làm dấu vết (lần lỗi sau ghi đè). Không mở lại `completed`/`rejected`. Log `event_delivery_retried` từng cặp và một dòng tổng kèm số lượng |
| `replay_events` | `--type` và `--since` (ISO datetime) bắt buộc; `--handler` tuỳ chọn, mặc định mọi handler đang đăng ký cho `(event_type, schema_version)` của từng sự kiện; tên handler không đăng ký → `CommandError`. Sự kiện `occurred_at ≥ since` đã có `deliveries_created_at`: tạo delivery còn thiếu bằng `bulk_create(ignore_conflicts=True)`; delivery đã có giữ nguyên (kể cả `failed`, `completed`). Sự kiện chưa có marker: bỏ qua, relay sẽ lập danh sách. Lô 100 sự kiện, mỗi lô một transaction. Tách đoạn dựng delivery trong `relay.create_deliveries` thành helper `build_deliveries(event, handlers, now)` dùng chung |
| `purge_old_outbox_events` | Celery task trong `shared/tasks.py`, `name="shared.purge_old_outbox_events"`, queue `default`; `beat_schedule` trong `config/celery.py` key `shared.purge_old_outbox_events`, `crontab(hour=3, minute=30)` theo `CELERY_TIMEZONE`. Hằng `OUTBOX_RETENTION = 90 ngày` theo `occurred_at`. Chỉ xoá sự kiện đã có marker và không còn delivery `pending`/`failed` (sự kiện có marker mà không có delivery cũng xoá); delivery bị xoá theo `CASCADE`. Xoá theo lô 1.000, mỗi lô một transaction, tới khi hết. Còn sự kiện quá 90 ngày bị giữ → log `WARNING` `outbox_purge_kept_unfinished` kèm số lượng. Sentry Cron check-in: khi cấu hình Sentry |
| Test | `shared/events/tests/`: `test_selectors.py`, `test_retry_failed_events.py`, `test_replay_events.py`, `test_purge.py`; seam là `call_command(...)`, gọi task trực tiếp và hàm public. Dữ liệu bằng `OutboxEventFactory`, `EventDeliveryFactory`; thời gian cố định bằng `time-machine`, purge kiểm cả hai phía mốc 90 ngày |
| Mode | full: 4 AC (vượt ngưỡng lite) |

## Kế hoạch

Sinh bằng `plan.py` từ state của skill. Mỗi task là đúng một commit có trailer `Task: <task>`.

| Task | AC | Seam | Test dự kiến | File | Sau |
| --- | --- | --- | --- | --- | --- |
| S1 | 3, 4 | shared.events.delivery_lag(), shared.events.get_delivery_outcomes() | `shared/events/tests/test_selectors.py::test_delivery_lag_zero_without_backlog`<br>`shared/events/tests/test_selectors.py::test_delivery_lag_counts_unlisted_event_and_due_pending`<br>`shared/events/tests/test_selectors.py::test_delivery_lag_ignores_failed_finished_and_future_retry`<br>`shared/events/tests/test_selectors.py::test_get_delivery_outcomes_reports_each_requested_handler` | `backend/shared/events/selectors.py`<br>`backend/shared/events/__init__.py`<br>`backend/shared/events/tests/test_selectors.py` | — |
| S2 | 1, 4 | call_command("retry_failed_events", ...) rồi process_delivery | `shared/events/tests/test_retry_failed_events.py::test_reopens_failed_and_next_run_succeeds`<br>`shared/events/tests/test_retry_failed_events.py::test_resets_schedule_and_counter_and_sets_retried_at`<br>`shared/events/tests/test_retry_failed_events.py::test_does_not_reopen_completed_or_rejected`<br>`shared/events/tests/test_retry_failed_events.py::test_filters_select_only_matching_pairs`<br>`shared/events/tests/test_retry_failed_events.py::test_requires_a_filter` | `backend/shared/events/operations.py`<br>`backend/shared/management/commands/retry_failed_events.py`<br>`backend/shared/events/tests/test_retry_failed_events.py` | S1 |
| S3 | 4 | call_command("replay_events", type=..., since=...) | `shared/events/tests/test_replay_events.py::test_replay_adds_delivery_for_new_handler`<br>`shared/events/tests/test_replay_events.py::test_replay_keeps_existing_deliveries`<br>`shared/events/tests/test_replay_events.py::test_replay_skips_event_not_yet_listed`<br>`shared/events/tests/test_replay_events.py::test_replay_unknown_handler_errors` | `backend/shared/events/relay.py`<br>`backend/shared/events/operations.py`<br>`backend/shared/management/commands/replay_events.py`<br>`backend/shared/events/tests/test_replay_events.py` | S2 |
| S4 | 2, 4 | task shared.purge_old_outbox_events gọi trực tiếp; app.conf.beat_schedule | `shared/events/tests/test_purge.py::test_purge_keeps_events_with_pending_or_failed`<br>`shared/events/tests/test_purge.py::test_purge_deletes_old_finished_events_and_deliveries`<br>`shared/events/tests/test_purge.py::test_purge_respects_retention_boundary`<br>`shared/events/tests/test_purge.py::test_purge_keeps_old_event_not_yet_listed`<br>`shared/events/tests/test_purge.py::test_purge_twice_same_result`<br>`shared/events/tests/test_purge.py::test_purge_scheduled_daily_0330` | `backend/shared/tasks.py`<br>`backend/config/celery.py`<br>`backend/shared/events/operations.py`<br>`backend/shared/events/tests/test_purge.py` | S3 |

Commit dự kiến: `plan` → `S1` → `S2` → `S3` → `S4` → `R1 (khi review cần sửa)` → `sync` → `close`.

## Acceptance criteria

- [ ] `retry_failed_events` mở lại delivery `failed` và lần chạy sau thành công.
- [ ] Purge không xoá sự kiện còn delivery `pending` hoặc `failed`.
- [ ] `get_delivery_outcomes` trả đúng trạng thái của từng handler được hỏi.
- [ ] Các kịch bản ở [07 mục 5](../../../docs/architecture/07-async-events-jobs.md#5-kịch-bản-kiểm-thử) về lệnh vận hành và purge đều có test.
