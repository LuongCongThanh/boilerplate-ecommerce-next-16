# Khung project backend: pyproject, settings, Compose, Makefile, health check

Status: ready-for-agent

Spec: [spec.md](../spec.md)

## Việc cần làm

- Tạo `backend/` theo cây thư mục ở [02 mục 5](../../../docs/architecture/02-backend-structure.md#5-cây-thư-mục), chỉ gồm phần M0 cần:
  - `pyproject.toml` với `[tool.uv] package = false`, cấu hình ruff, mypy, pytest, import-linter đúng như 02 mục 8 và 9.3 (`target-version = "py314"`, `python_version = "3.14"`); `.python-version` = `3.14`; `uv.lock`.
  - Dependency runtime của M0: `django` 5.2.x, `djangorestframework`, `drf-spectacular`, `psycopg[binary,pool]`, `redis`, `celery`, `django-celery-beat`, `pydantic`, `pydantic-settings`, `structlog`, `django-structlog`, `sentry-sdk[django,celery]`, `gunicorn`. Dependency dev theo 02 mục 3.2.
  - `config/env.py` (pydantic-settings, đủ biến ở [08 mục 2.3](../../../docs/architecture/08-local-development.md#23-biến-môi-trường)), `config/settings/{base,local,test,production}.py`, `config/urls.py`, `config/celery.py`, `config/wsgi.py`.
  - App `shared` và app `modules`; `modules/<module>/__init__.py` cho 8 module con, chưa có model.
  - `.env.example` khớp 08 mục 2.3, không chứa secret thật.
- `Dockerfile` một image cho api, worker, beat, relay (cài bằng `uv sync --locked --no-build`). `docker-compose.yml` gồm api, worker, beat, relay, redis (Valkey 8), mailpit; không có service postgres; pin image tới bản vá.
- `Makefile` với các lệnh ở [08 mục 3](../../../docs/architecture/08-local-development.md#3-lệnh-hằng-ngày-makefile).
- `/healthz` và `/readyz` theo [04 mục 4.4](../../../docs/architecture/04-api-contract.md#44-vận-hành).
- `scripts/gen_importlinter.py` sinh contract `forbidden` cho mọi cặp module và có chế độ `--check` cho CI (02 mục 8). Contract `layers` đã có trong `pyproject.toml`.
- Kiểm tra cờ của `cz` theo bản `commitizen` được pin, gỡ nhãn **[Cần xác minh]** ở [11](../../../docs/architecture/11-git-workflow.md).
- Một smoke test: Django khởi động với `config.settings.test`, `/healthz` trả 200, `/readyz` trả 200 khi có DB.

## Acceptance criteria

- [ ] `make up` chạy đủ các service; `curl localhost:8000/healthz` và `/readyz` trả 200.
- [ ] `make lint` (ruff check, ruff format --check, mypy, lint-imports, `gen_importlinter.py --check`) và `make test` qua ở local.
- [ ] Job `backend` trong `.github/workflows/ci.yml` bắt đầu chạy thật (đã có `backend/pyproject.toml`) và xanh.
- [ ] `pre-commit run --all-files` chạy ruff, mypy, import-linter trên `backend/` và qua.
- [ ] Thiếu một biến bắt buộc trong `.env` thì Django báo lỗi rõ tên biến ngay khi khởi động.
- [ ] Tài liệu nào lệch với cái đã làm (lệnh Makefile, biến môi trường, phiên bản pin) được sửa trong cùng PR.
