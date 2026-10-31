# Báo cáo

- 29/10/2026: Kiểm tra trên Windows 11, nhánh `feat/backend-skeleton`:
  - Máy không có `make`, nên chạy từng lệnh tương đương trong `make lint` và `make test`. Windows Application Control chặn file `.exe` trong `.venv`, nên gọi qua `python -m` (`mypy`, `importlinter`, `pytest`, `pre_commit`). CI chạy trên Linux nên không bị ảnh hưởng.
  - ruff, mypy, lint-imports qua. 5 test qua trên PostgreSQL 18.6 (container tạm), cả khi chạy tuần tự lẫn `-n 2`. `migrate` và `manage.py check` qua với cả `local` lẫn `production`. `pip-audit --strict` không có lỗ hổng.
  - `pre-commit run --all-files`: ruff, mypy, import-linter, gitleaks qua. `check-toml` và `trailing-whitespace` báo Failed không kèm lỗi, do App Control chặn file chạy của hook; kiểm tra tay thì `pyproject.toml` và `uv.lock` parse được, không có dòng nào thừa khoảng trắng cuối.
  - `cz` 4.19.3: `--files-only` đã deprecate, `11` đổi sang `--version-files-only`.
  - Không cài `django.contrib.auth`, `sessions`, `admin`; DRF tạm để `UNAUTHENTICATED_USER = None` cho tới khi có JWT ở M1.
  - Bỏ extra `compatible-mypy` của các gói stub vì `djangorestframework-stubs` giới hạn `mypy<2.4`; đã ghi vào `02` mục 3.2.
  - Job `backend` xanh trên PR #20, dùng `postgres:18.6` và `valkey/valkey:8.1.11` của `services:`.
