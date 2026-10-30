# Lệnh vận hành và theo dõi outbox

Status: resolved

**PR:** #38

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
| `retry_failed_events` | Bộ lọc `--event-id`, `--handler`, `--type` kết hợp được, hoặc `--all`; không có bộ lọc nào → `CommandError`. Khoá bằng `select_for_update`, chỉ lấy dòng còn `failed`; đặt `pending`, `attempts = 0`, `next_attempt_at = next_dispatch_at = now`, `retried_at = now`. Giữ `failed_at`, `last_error` làm dấu vết (lần lỗi sau ghi đè). Không mở lại `completed`/`rejected`. Log `event_delivery_retried` từng cặp và một dòng tổng kèm số lượng. Thêm khi review (B2/B8, T4): `--handler` chưa đăng ký → `CommandError`; delivery có handler không còn trong registry thì không mở lại (mở lại sẽ kẹt `pending` mãi và đẩy `delivery_lag` lên), log `WARNING` `event_delivery_retry_skipped`; hàm trong `operations.py` tên `retry_failed_events`, trùng tên lệnh |
| `replay_events` | `--type` và `--since` (ISO datetime) bắt buộc; `--handler` tuỳ chọn, mặc định mọi handler đang đăng ký cho `(event_type, schema_version)` của từng sự kiện; tên handler không đăng ký, hoặc không đăng ký cho `--type` → `CommandError` (thêm khi review, B6). Sự kiện có `deliveries_created_at ≥ since`: tạo delivery còn thiếu (đổi khi review, B1: khoảng hở khi deploy là lúc relay cũ lập danh sách, không phải lúc sự kiện xảy ra; sự kiện phát ngay trước mốc deploy nhưng được lập danh sách sau mốc vẫn phải được phát lại). Mỗi lô khoá sự kiện bằng `select_for_update` để purge chạy đồng thời không xoá sự kiện giữa chừng; purge khoá theo thứ tự `id` như replay (thêm khi review, B4). Log ghi số sự kiện đã xét và số delivery tạo mới (thêm khi review, B6/T5) bằng `bulk_create(ignore_conflicts=True)`; delivery đã có giữ nguyên (kể cả `failed`, `completed`). Sự kiện chưa có marker: bỏ qua, relay sẽ lập danh sách. Lô 100 sự kiện, mỗi lô một transaction. Tách đoạn dựng delivery trong `relay.create_deliveries` thành helper `build_deliveries(event, handlers, now)` dùng chung |
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

- [x] `retry_failed_events` mở lại delivery `failed` và lần chạy sau thành công.
- [x] Purge không xoá sự kiện còn delivery `pending` hoặc `failed`.
- [x] `get_delivery_outcomes` trả đúng trạng thái của từng handler được hỏi.
- [x] Các kịch bản ở [07 mục 5](../../../docs/architecture/07-async-events-jobs.md#5-kịch-bản-kiểm-thử) về lệnh vận hành và purge đều có test.

## Comments

### Báo cáo 30/10/2026

**Nhánh:** `feat/outbox-operations` · **PR:** #38 · **Mode:** full

#### Đã làm

| AC | Bằng chứng |
| --- | --- |
| 1. `retry_failed_events` mở lại delivery `failed`, lần chạy sau thành công | `shared/events/tests/test_retry_failed_events.py::test_reopens_failed_and_next_run_succeeds`, `::test_resets_schedule_and_counter_and_sets_retried_at`, `::test_all_reopens_every_failed_delivery` |
| 2. Purge không xoá sự kiện còn delivery `pending`/`failed` | `shared/events/tests/test_purge.py::test_purge_keeps_events_with_pending_or_failed`, `::test_purge_keeps_old_event_not_yet_listed`; purge chạy đồng thời replay: `test_replay_events.py::test_replay_and_purge_concurrently_keep_new_delivery` (PostgreSQL thật, hai thread) |
| 3. `get_delivery_outcomes` trả đúng trạng thái từng handler được hỏi | `shared/events/tests/test_selectors.py::test_get_delivery_outcomes_reports_each_requested_handler` |
| 4. Kịch bản 07 §5 về lệnh vận hành và purge có test | `delivery_lag`: `test_selectors.py` (3 test, gồm bảng 07 §5). `retry_failed_events`: `test_retry_failed_events.py` (8 test: mở lại rồi chạy thành công, reset lịch/bộ đếm/`retried_at`, không mở lại `completed`/`rejected`, bộ lọc, `--all`, thiếu bộ lọc, handler chưa đăng ký). Replay: `test_replay_events.py` (7 test: thêm handler mới tạo delivery, giữ delivery đã có, bỏ qua sự kiện chưa lập danh sách, chọn theo `deliveries_created_at` kể cả đúng mốc, handler lạ hoặc khác loại sự kiện, chạy đồng thời purge). Purge: `test_purge.py` (6 test: giữ `pending`/`failed`, xoá sự kiện đã xong cùng delivery, hai phía mốc 90 ngày, giữ sự kiện chưa lập danh sách kèm `WARNING`, chạy hai lần cùng kết quả, lịch Beat 03:30) |

`make lint` xanh (ruff, mypy, import-linter 1 kept / 0 broken) · `make test`: 237 passed trong 9.17s

#### Chưa làm

- Sentry Cron check-in của `purge_old_outbox_events` (07 §3.4): chờ cấu hình Sentry.

#### Gap

- `replay_events --since` không ghi múi giờ thì hiểu theo `TIME_ZONE` (Asia/Ho_Chi_Minh); ghi vào 07 ở phase sync.
- Delivery mồ côi đẩy `delivery_lag` lên mãi, purge quét toàn bảng khi tồn đọng lớn, `occurred_at` thay cho giờ ghi DB, `retry_failed_events --all` không chia lô: ticket [28](./28-outbox-operations-hardening.md) (`needs-triage`).

#### Thay đổi theo yêu cầu

- 30/10/2026, SonarCloud `test_purge.py:47`, `test_retry_failed_events.py:53` (trộn hai thứ tự đối số assert trong một file): vế trái bắt đầu bằng tên viết hoa (`operations.OUTBOX_RETENTION`, `EventDelivery.objects…`) bị coi là giá trị kỳ vọng; gán vào biến thường rồi assert `actual == expected`, bỏ `# noqa: SIM300`. Hành vi test không đổi.

#### Review

Ba trục: Spec, Standards, Bug (`/code-review high`). Vòng sửa R1 (`02cc7f9`), 237 test xanh.

| Mã | Chỗ | Kết luận | Lý do |
| --- | --- | --- | --- |
| B1 | `shared/events/operations.py` | đã sửa | Replay chọn sự kiện theo `deliveries_created_at ≥ since`: khoảng hở khi deploy là lúc relay cũ lập danh sách; đổi `## Quyết định` |
| B4, S5 | `shared/events/operations.py` | đã sửa | Replay khoá lô sự kiện, purge khoá theo `id`; có test đồng thời trên PostgreSQL thật |
| B6, S6, T5 | `replay_events.py`, `operations.py` | đã sửa | `--handler` khác `--type` → `CommandError`; log ghi `examined` và `created`, hàm trả số delivery tạo mới |
| B2, B8 | `retry_failed_events.py`, `operations.py` | đã sửa | `--handler` chưa đăng ký → `CommandError`; không mở lại delivery của handler đã gỡ, log `WARNING` `event_delivery_retry_skipped` |
| T4 | `shared/events/operations.py` | đã sửa | Hàm đổi tên `retry_failed_events`, một thao tác một tên (02 §9.2) |
| T1, S1, S2 | test | đã sửa | Chiều assert; test `--all`; assert mốc `since` và `WARNING` khi giữ sự kiện chưa lập danh sách |
| B3, B5, B7, B9 | `selectors.py`, `operations.py` | chỉ báo | Cần migration hoặc đổi consumer → ticket [28](./28-outbox-operations-hardening.md) |
| B10, T6, T7 | test, `selectors.py` | chỉ báo | Helper test lặp, điều kiện "tới hạn" thứ ba → bổ sung ticket [26](./26-outbox-refactor-smells.md) |
| T2, T3 | `operations.py`, `selectors.py` | chỉ báo | Transaction trong `operations.py`, tên `get_delivery_outcomes` đã chốt ở 07: ghi ngoại lệ vào 02 §9.1, §9.2 ở phase sync |
| S3, S4 | `tasks.py`, `replay_events.py` | chỉ báo | Sentry Cron chờ cấu hình Sentry; múi giờ của `--since` ghi vào 07 |
| — | `replay_events.py`, `retry_failed_events.py` | bác | In kết quả ra stdout: lệnh của `shared` chỉ log qua structlog (02 §9.6), log đã có số lượng |

#### Commit

| Task | Phase | AC | Commit | File |
| --- | --- | --- | --- | --- |
| plan | 1 grill | — | `a5ca5b4` docs: plan outbox operations ticket | 1 |
| S1 | 2 code | 3, 4 | `23ef59e` feat(shared): add delivery_lag and get_delivery_outcomes selectors | 3 |
| S2 | 2 code | 1, 4 | `951809c` feat(shared): add retry_failed_events command | 3 |
| S3 | 2 code | 4 | `a1fd31c` feat(shared): add replay_events command | 4 |
| S4 | 2 code | 2, 4 | `4855612` feat(shared): add purge_old_outbox_events job | 4 |
| R1 | 4 review | — | `02cc7f9` fix(shared): address review findings on outbox operations | 6 |

#### Tài liệu đã cập nhật

- `docs/architecture/07-async-events-jobs.md` §1.1.1: `delivery_lag` trả `timedelta`, tính theo `occurred_at` (thay `created_at` không có trong bảng); dạng trả về của `get_delivery_outcomes`; `replay_events` chọn theo `deliveries_created_at ≥ --since`, múi giờ của `--since`, `--handler` đúng loại, khoá lô sự kiện. §1.3: bộ lọc của `retry_failed_events`, giữ `failed_at`/`last_error`, không mở lại handler đã gỡ.
- `docs/architecture/02-backend-structure.md` §5: `shared/events/selectors.py`, `operations.py`, `relay.build_deliveries`; §9.1: transaction trong relay và `operations.py` của `shared.events`; §9.2: ngoại lệ tên `get_delivery_outcomes`, `delivery_lag`.
- `backend/shared/tests/test_sync_beat_schedule.py`: comment fixture không còn nói `beat_schedule` rỗng.
- `.scratch/mvp-roadmap/map.md`: Decisions-so-far về API theo dõi outbox.
- Ticket mới `needs-triage`: [28](./28-outbox-operations-hardening.md). Bổ sung ticket [26](./26-outbox-refactor-smells.md) (helper test, điều kiện "tới hạn").
