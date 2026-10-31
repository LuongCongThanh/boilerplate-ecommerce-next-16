# Báo cáo

### Báo cáo 31/10/2026

**Nhánh:** `fix/outbox-killed-delivery-redispatch` · **PR:** chưa mở · **Mode:** full

#### Đã làm

| AC | Bằng chứng |
| --- | --- |
| 1. Handler luôn vượt time limit thì delivery cuối cùng chuyển `failed` và có log `ERROR`, không giao lại vô hạn | `shared/events/tests/test_consumer.py::test_interrupted_handler_fails_after_max_interrupted_runs`, `shared/events/tests/test_consumer.py::test_saved_outcome_resets_interrupted_runs`, `shared/events/tests/test_consumer.py::test_handler_breaking_connection_rolls_back_whole_transaction`, `shared/events/tests/test_consumer.py::test_concurrent_duplicate_dispatch_commits_once`, `shared/events/tests/test_retry_failed_events.py::test_reopens_interrupted_delivery_with_counter_reset` |
| 2. Task mất do Redis (không phải do handler) vẫn không tiêu lượt retry | `shared/events/tests/test_relay.py::test_lost_tasks_do_not_count_as_interrupted_runs`, `shared/events/tests/test_consumer.py::test_missing_handler_keeps_pending_without_attempt` |

Worker bị kill được giả lập bằng handler ném một `BaseException` con: `except Exception` của consumer không bắt, transaction 2 rollback, giống process chết giữa chừng. Test của AC2 được chứng minh bắt đúng lỗi bằng cách tạm cho relay tăng bộ đếm (cách đã loại): test đỏ với `interrupted_runs=4`, rồi hoàn tác.

`make lint` xanh · `make test`: 315 passed

#### Chưa làm

- Chưa kiểm tay với Celery worker thật (handler `sleep` quá 120 giây trong Compose). Test chỉ giả lập process bị kill ở seam `process_delivery()`.

#### Gap

- Rủi ro chấp nhận (review S2/B2, B3): gián đoạn không do handler (kết nối DB hỏng, cold shutdown, OOM do task khác) và task trùng chen giữa hai transaction sát ngưỡng có thể làm delivery `failed` sớm; có cảnh báo, mở lại bằng `retry_failed_events`.
- Mỗi delivery tốn thêm một transaction và một `UPDATE` trước khi chạy handler. Thông lượng relay là việc của ticket 25.

#### Thay đổi theo yêu cầu

- Không

#### Review

Ba trục: Standards 2 vi phạm cứng (T1, T2), 2 chỗ tài liệu lệch (T3, T4), 4 smell (T5–T8); Spec 4 finding (S1–S4); Bug 8 finding (B1–B8). Mọi mục được chọn đã sửa trong R1.

| Mã | Chỗ | Kết luận | Lý do |
| --- | --- | --- | --- |
| B1 | `backend/shared/migrations/0005_event_delivery_interrupted_runs.py` | đã sửa | `default=0` sinh `DROP DEFAULT`, relay bản cũ INSERT lỗi NOT NULL khi rolling deploy (09 §104); giờ `db_default=0` |
| T1, T2 | `backend/shared/events/tests/test_consumer.py` | đã sửa | Gán tuple vào biến trước khi assert (CONTRIBUTING) |
| B5 | `test_consumer.py` | đã sửa | Test AC1 chạy `django_db(transaction=True)` để chứng minh bộ đếm commit thật |
| S1 | `test_consumer.py` | đã sửa | Test task trùng assert `interrupted_runs == 0` |
| S4/T8, T7 | test | đã sửa | Comment dạng điều kiện; dùng hằng `INTERRUPTED_ERROR` |
| S3/B7/T3, T4 | `docs/architecture/07-async-events-jobs.md` §5, §1.1, §1.3 | đã sửa | Thêm kịch bản test; câu bảo đảm nêu giới hạn 3 lần; nêu rõ `attempts` |
| S2/B2 | `backend/shared/events/consumer.py` | chỉ báo, rủi ro chấp nhận | Task trùng chen giữa hai transaction sát ngưỡng làm `failed` sớm một lần; ghi ở Quyết định và 07 §1.1.1 |
| B3 | `consumer.py` | chỉ báo, rủi ro chấp nhận | Gián đoạn không do handler cũng tính; cần 3 lần liên tiếp; ghi ở Quyết định và 07 §1.1.1 |
| B6, T5, T6/B8 | `consumer.py` | đã sửa | Transaction 2 khoá theo `pk`; helper `_mark_failed`; reset bộ đếm và `save` gom một chỗ |
| B4 | `consumer.py` | bác | Guard `in_atomic_block` làm hỏng test (pytest-django bọc atomic); Celery không gọi consumer trong atomic |

#### Commit

| Task | Phase | AC | Commit | File |
| --- | --- | --- | --- | --- |
| plan | 1 grill | — | `6656a0e` docs: plan outbox interrupted delivery ticket | 2 |
| S1 | 2 code | 1, 2 | `a8f27e2` fix(shared): fail deliveries whose handler keeps getting killed | 7 |
| S2 | 2 code | 1 | `8a113fc` fix(shared): reset interrupted runs when retrying failed deliveries | 2 |
| R1 | 4 review | — | `5498592` fix(shared): address review findings on interrupted deliveries | 8 |

#### Tài liệu đã cập nhật

- `docs/architecture/03-data-model.md` §1.4: cột `interrupted_runs`, `CHECK`, `retry_failed_events` đặt về 0
- `docs/architecture/07-async-events-jobs.md` §1, §1.1, §1.1.1, §1.3, §5: consumer chạy hai transaction, quy tắc lần chạy dở, ngưỡng 3, `HandlerInterrupted`, rủi ro chấp nhận, kịch bản test
- `.scratch/backend-bootstrap/issues/26-outbox-refactor-smells/spec.md`: danh sách hàm chuyển trạng thái của consumer sau ticket này
