# Kế hoạch

Sinh bằng `plan.py` từ state của skill. Mỗi task là đúng một commit có trailer `Task: <task>`.

| Task | AC | Seam | Test dự kiến | File | Sau |
| --- | --- | --- | --- | --- | --- |
| S1 | 1, 2, 3 | database_config() và manage.py check qua subprocess | `tests/test_database_url.py::test_rejects_malformed_url`<br>`tests/test_database_url.py::test_error_message_hides_url_and_password`<br>`tests/test_database_url.py::test_manage_py_check_stops_before_connecting`<br>`tests/test_database_url.py::test_keeps_query_parameters_as_options`<br>`tests/test_database_url.py::test_allows_url_without_password`<br>`tests/test_database_url.py::test_host_argument_overrides_host_of_url` | `backend/config/env.py`<br>`backend/tests/test_database_url.py` | — |

Commit dự kiến: `plan` → `S1` → `R1 (khi review cần sửa)` → `sync` → `close`.
