# Báo cáo

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
- Delivery mồ côi đẩy `delivery_lag` lên mãi, purge quét toàn bảng khi tồn đọng lớn, `occurred_at` thay cho giờ ghi DB, `retry_failed_events --all` không chia lô: ticket [28](../28-outbox-operations-hardening/spec.md) (`needs-triage`).

#### Thay đổi theo yêu cầu

- 30/10/2026, SonarCloud `test_purge.py:47`, `test_retry_failed_events.py:53` (trộn hai thứ tự đối số assert trong một file): Sonar coi tuple/list ở vế trái so với một tên biến (`(…) == before`, `(…) == after_first`) là giá trị kỳ vọng đặt trước. Gán tuple vào biến (`after`, `after_second`) rồi assert `actual == expected`; lần đầu (`7aeaf9c`) đoán nhầm nguyên nhân là tên viết hoa, vẫn sửa thêm `OUTBOX_RETENTION`/`count()` và bỏ `# noqa: SIM300`. Hành vi test không đổi.

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
| B3, B5, B7, B9 | `selectors.py`, `operations.py` | chỉ báo | Cần migration hoặc đổi consumer → ticket [28](../28-outbox-operations-hardening/spec.md) |
| B10, T6, T7 | test, `selectors.py` | chỉ báo | Helper test lặp, điều kiện "tới hạn" thứ ba → bổ sung ticket [26](../26-outbox-refactor-smells/spec.md) |
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
- Ticket mới `needs-triage`: [28](../28-outbox-operations-hardening/spec.md). Bổ sung ticket [26](../26-outbox-refactor-smells/spec.md) (helper test, điều kiện "tới hạn").
