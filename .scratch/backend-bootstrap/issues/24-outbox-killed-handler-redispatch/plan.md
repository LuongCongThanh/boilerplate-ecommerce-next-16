# Kế hoạch

Sinh bằng `plan.py` từ state của skill. Mỗi task là đúng một commit có trailer `Task: <task>`.

| Task | AC | Seam | Test dự kiến | File | Sau |
| --- | --- | --- | --- | --- | --- |
| S1 | 1, 2 | process_delivery() với handler ném BaseException giả lập worker bị kill; dispatch_due() với apply_async không giao (task mất) | `shared/events/tests/test_consumer.py::test_interrupted_handler_fails_after_max_interrupted_runs`<br>`shared/events/tests/test_consumer.py::test_saved_outcome_resets_interrupted_runs`<br>`shared/events/tests/test_consumer.py::test_missing_handler_keeps_pending_without_attempt`<br>`shared/events/tests/test_relay.py::test_lost_tasks_do_not_count_as_interrupted_runs`<br>`shared/events/tests/test_consumer.py::test_concurrent_duplicate_dispatch_commits_once` | `backend/shared/events/models.py`<br>`backend/shared/migrations/0005_event_delivery_interrupted_runs.py`<br>`backend/shared/events/consumer.py`<br>`backend/shared/events/tests/test_consumer.py`<br>`backend/shared/events/tests/test_relay.py`<br>`docs/architecture/03-data-model.md`<br>`docs/architecture/07-async-events-jobs.md` | — |
| S2 | 1 | call_command(retry_failed_events) trên delivery failed vì chạy dở | `shared/events/tests/test_retry_failed_events.py::test_reopens_interrupted_delivery_with_counter_reset` | `backend/shared/events/operations.py`<br>`backend/shared/events/tests/test_retry_failed_events.py` | S1 |

Commit dự kiến: `plan` → `S1` → `S2` → `R1 (khi review cần sửa)` → `sync` → `close`.
