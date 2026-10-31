# Báo cáo

### Báo cáo 31/10/2026

**Nhánh:** `fix/validate-database-url` · **PR:** #45 · **Mode:** lite

#### Đã làm

| AC | Bằng chứng |
| --- | --- |
| 1. `DATABASE_URL` thiếu user, thiếu host hoặc tên database sai làm `manage.py check` và pytest dừng ngay với `ImproperlyConfigured` | `tests/test_database_url.py::test_rejects_malformed_url` (11 trường hợp, gồm password chứa `/` và `///fashion`), `tests/test_database_url.py::test_manage_py_check_stops_before_connecting` |
| 2. Thông báo lỗi không chứa password hay toàn bộ URL | `tests/test_database_url.py::test_error_message_hides_url_and_password` (kiểm cả traceback có exception nối chuỗi, ở nhánh thiếu user và nhánh port), `tests/test_database_url.py::test_manage_py_check_stops_before_connecting` |
| 3. Các test hiện có của `test_database_url.py` vẫn pass | `tests/test_database_url.py::test_keeps_query_parameters_as_options`, `tests/test_database_url.py::test_allows_url_without_password`, `tests/test_database_url.py::test_host_argument_overrides_host_of_url`, `tests/test_database_url.py::test_invalid_port_raises_improperly_configured` |

Với `env.py` cũ, các test mới cho AC 1 và 2 đều đỏ (`manage.py check` exit 0 với URL hỏng), nên chúng bắt đúng lỗi của ticket.

`make lint` xanh · `make test`: 308 passed trong 9.70s

#### Chưa làm

- Không

#### Gap

- Test subprocess phải đặt `PYTHONUTF8=1` cho process con, vì trên Windows output bị chuyển hướng mặc định ghi bằng `cp1252`. Cùng nguyên nhân với ticket 23 (`make lint` lỗi mã hoá trên Windows); ticket 23 sửa ở `Makefile`, không bỏ được dòng này vì test gọi thẳng `sys.executable`.
- URL Unix socket (`postgres://u@/db?host=/var/run/postgresql`) và peer-auth (không user) giờ bị từ chối, theo đúng ticket. Repo hiện chỉ dùng URL có user và host (local, CI, RDS); nếu sau này cần socket thì phải nới điều kiện.

#### Thay đổi theo yêu cầu

- Không

#### Review

Ba trục: Spec không có finding; Standards 3 judgement call (T1–T3); Bug 9 finding (B1–B9).

| Mã | Chỗ | Kết luận | Lý do |
| --- | --- | --- | --- |
| B1 | `backend/config/env.py:93` | đã sửa | Lỗi port nối `ValueError` của urllib làm lộ password trong traceback; giờ `from None` |
| B4 | `backend/tests/test_database_url.py:62` | đã sửa | Test AC2 kiểm cả traceback, thêm trường hợp tới nhánh port |
| B5 | `backend/config/env.py:94` | đã sửa | `lstrip` nhận `///fashion`; đổi sang `removeprefix` |
| B2 | `backend/config/env.py:90` | đã sửa | Kiểm user, host, tên database trước port; sửa dòng Quyết định |
| B8, T1, T2, T3 | `env.py`, `test_database_url.py` | đã sửa | Bỏ biến cờ, đổi tên `missing` → `problem`, hằng `MISPLACED_PASSWORD_URL`, docstring `Raises:` |
| B3 | `backend/config/env.py:99` | bác | Từ chối URL không user/host là yêu cầu của ticket; ghi ở Gap |
| B6 | `backend/config/env.py:101` | bác | Ticket yêu cầu từ chối `:`, `@` trong tên database |
| B7 | `backend/tests/test_database_url.py:82` | bác | Test subprocess đã chốt ở G1, tốn khoảng 0,4 giây |
| B9 | `.scratch/backend-bootstrap/issues/24…28` | bác | Skill quy định commit dòng `Status:` đã triage cùng commit plan |

#### Commit

| Task | Phase | AC | Commit | File |
| --- | --- | --- | --- | --- |
| plan | 1 grill | — | `81d167b` docs: plan database url validation ticket | 7 |
| S1 | 2 code | 1, 2, 3 | `c34b11b` fix(config): reject malformed DATABASE_URL at startup | 2 |
| R1 | 4 review | — | `69e1f2d` fix(config): address review findings on database url validation | 3 |

#### Tài liệu đã cập nhật

- `docs/architecture/08-local-development.md` mục 2.3: `DATABASE_URL` sai định dạng làm Django dừng ngay, password có ký tự đặc biệt phải mã hoá phần trăm
