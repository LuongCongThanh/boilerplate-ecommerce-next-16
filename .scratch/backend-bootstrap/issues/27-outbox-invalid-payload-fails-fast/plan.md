# Kế hoạch

Sinh bằng `plan.py` từ state của skill. Mỗi task là đúng một commit có trailer `Task: <task>`.

| Task | AC | Seam | Test dự kiến | File | Sau |
| --- | --- | --- | --- | --- | --- |
| S1 | 1, 2 | process_delivery(event_id, handler) trên delivery có payload thiếu/sai field, và handler tự ném pydantic.ValidationError | `shared/events/tests/test_consumer.py::test_invalid_payload_fails_without_calling_handler`<br>`shared/events/tests/test_consumer.py::test_validation_error_inside_handler_schedules_retry` | `backend/shared/events/consumer.py`<br>`backend/shared/events/tests/test_consumer.py`<br>`docs/architecture/07-async-events-jobs.md` | — |

Commit dự kiến: `plan` → `S1` → `R1 (khi review cần sửa)` → `sync` → `close`.
