# Khung project backend: pyproject, settings, Compose, Makefile, health check

Status: ready-for-agent

Spec: [spec.md](../spec.md)

## Việc cần làm

- Tạo `backend/` theo cây thư mục ở [02 mục 5](../../../docs/architecture/02-backend-structure.md#5-cây-thư-mục), chỉ gồm phần M0 cần:
  - `pyproject.toml` với `[tool.uv] package = false`, cấu hình ruff, mypy, pytest, import-linter đúng như 02 mục 8 và 9.3 (`target-version = "py314"`, `python_version = "3.14"`); `.python-version` = `3.14`; `uv.lock`.
  - Dependency runtime của M0: `django` 5.2.x, `djangorestframework`, `drf-spectacular`, `psycopg[binary,pool]`, `redis`, `celery`, `django-celery-beat`, `pydantic`, `pydantic-settings`, `structlog`, `django-structlog`, `sentry-sdk[django,celery]`, `gunicorn`. Dependency dev theo 02 mục 3.2.
  - `config/env.py` (pydantic-settings) chỉ khai báo các biến nhóm "Từ M0" ở [08 mục 2.3](../../../docs/architecture/08-local-development.md#23-biến-môi-trường); biến của mốc sau thêm ở mốc dùng tới. `config/settings/{base,local,test,production}.py`, `config/urls.py`, `config/celery.py`, `config/wsgi.py`.
  - App `shared` và app `modules`; `modules/<module>/__init__.py` cho 8 module con, chưa có model.
  - `.env.example` chỉ chứa các biến "Từ M0" của 08 mục 2.3, không chứa secret thật.
- `Dockerfile` một image cho api, worker, beat, relay (cài bằng `uv sync --locked --no-build`). `docker-compose.yml` gồm migrate, api, worker, beat, relay, redis (Valkey 8), mailpit theo [08 mục 7](../../../docs/architecture/08-local-development.md#7-docker-composeyml-rút-gọn): service `migrate` chạy `migrate` và `sync_beat_schedule` rồi thoát, các service app chờ nó thoát thành công; không có service postgres; pin image tới bản vá.
- `Makefile` với các lệnh có cột "Có từ" là ticket 07 ở [08 mục 3](../../../docs/architecture/08-local-development.md#3-lệnh-hằng-ngày-makefile): `up`, `down`, `logs`, `shell`, `makemigrations`, `migrate`, `db-reset`, `test`, `lint`, `fmt`. `load-geo` thêm ở ticket 09, `create-admin` ở ticket 12.
- Job `backend` trong `.github/workflows/ci.yml`:
  - Thêm `services:` gồm `postgres:18` và `valkey/valkey:8` (pin tới bản vá như Compose), có health check.
  - Thêm khối `env:` ở cấp job: `DJANGO_SETTINGS_MODULE=config.settings.test`, `DATABASE_URL`, `REDIS_URL` trỏ tới hai service trên, và giá trị giả cho các biến bắt buộc còn lại của M0. Không commit file `.env` cho CI.
  - Bước Lint chạy thêm `python scripts/gen_importlinter.py --check`, để CI chạy giống `make lint`.
- `/healthz` và `/readyz` theo [04 mục 4.4](../../../docs/architecture/04-api-contract.md#44-vận-hành).
- `scripts/gen_importlinter.py` sinh contract `forbidden` cho mọi cặp module và có chế độ `--check` cho CI (02 mục 8). Contract `layers` đã có trong `pyproject.toml`.
- Kiểm tra cờ của `cz` theo bản `commitizen` được pin, gỡ nhãn **[Cần xác minh]** ở [11](../../../docs/architecture/11-git-workflow.md).
- Một smoke test: Django khởi động với `config.settings.test`, `/healthz` trả 200, `/readyz` trả 200 khi có DB.

## Acceptance criteria

- [ ] Trên DB trống, `make up` chạy `migrate` trước rồi mới bật api, worker, beat, relay; không service nào khởi động lại liên tục. `curl localhost:8000/healthz` và `/readyz` trả 200 (cần ticket 08 xong để có PostgreSQL).
- [ ] `make lint` (ruff check, ruff format --check, mypy, lint-imports, `gen_importlinter.py --check`) và `make test` qua ở local.
- [ ] Job `backend` trong `.github/workflows/ci.yml` bắt đầu chạy thật (đã có `backend/pyproject.toml`), dùng PostgreSQL và Valkey của `services:`, chạy cả `gen_importlinter.py --check`, và xanh.
- [ ] `pre-commit run --all-files` chạy ruff, mypy, import-linter trên `backend/` và qua.
- [ ] Thiếu một biến bắt buộc của M0 trong `.env` thì Django báo lỗi rõ tên biến ngay khi khởi động. Không có biến nào của M1 trở đi bị bắt buộc.
- [ ] Tài liệu nào lệch với cái đã làm (lệnh Makefile, biến môi trường, phiên bản pin) được sửa trong cùng PR.
