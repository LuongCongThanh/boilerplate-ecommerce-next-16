# Docker Compose local, lệnh Makefile dùng container và `sync_beat_schedule`

Status: resolved

**PR:** #27

Spec: [spec.md](../spec.md)

Blocked by: 07, 08

## Bối cảnh

Tách từ ticket [07](./07-project-skeleton.md) để phần cần container gọi được PostgreSQL trên máy (ticket [08](./08-local-postgres-installer.md)) nằm riêng một chỗ, không chặn phần còn lại của khung project.

`sync_beat_schedule` nằm ở đây vì service `migrate` và `make migrate` gọi nó ([08 mục 7](../../../docs/architecture/08-local-development.md#7-docker-composeyml-rút-gọn)). Lệnh chỉ đồng bộ lịch Celery Beat, không phụ thuộc outbox. Service `relay` thêm vào Compose ở ticket [10](./10-shared-events-outbox.md), cùng lúc với lệnh `run_outbox_relay`.

## Việc cần làm

- `Dockerfile` một image cho worker, beat, relay, migrate (cài bằng `uv sync --locked --no-build`). API không chạy trong Compose mà chạy trên máy ([ADR 0017](../../../docs/adr/0017-windows-native-dev-api-on-host.md)).
- `docker-compose.yml` gồm migrate, worker, beat, redis (Valkey 8), mailpit theo 08 mục 7: service `migrate` chạy `migrate` và `sync_beat_schedule` rồi thoát, các service app chờ nó thoát thành công; không có service postgres, không có service api; container ghi đè `DATABASE_URL`, `REDIS_URL`, `EMAIL_HOST`; Redis mở ra máy ở `${REDIS_PORT:-6380}`; pin image tới bản vá.
- `backend/.env.example`: `.env` viết cho máy, thêm `REDIS_PORT=6380`, `REDIS_URL=redis://localhost:6380/0`, `EMAIL_HOST=localhost` (08 mục 2.3).
- `shared/management/commands/sync_beat_schedule.py`: ghi lịch job từ `config/celery.py` vào `django-celery-beat`, tắt job thừa ([07 mục 3.2](../../../docs/architecture/07-async-events-jobs.md)).
- Thêm vào `Makefile` các lệnh ở [08 mục 3](../../../docs/architecture/08-local-development.md#3-lệnh-hằng-ngày-makefile): `up`, `down`, `run`, `restart-worker`, `logs`, `shell`, `makemigrations`, `migrate`, `db-reset`. Recipe chỉ gọi `uv run` hoặc `docker compose`, chạy được bằng GNU make trên Windows.
- IDE: `.vscode/launch.json` thay "Attach Django (Docker)" bằng "Django (local)"; thêm `.run/Django server.run.xml` cho PyCharm; bỏ extension WSL khỏi `.vscode/extensions.json`.
- Bỏ `debugpy` khỏi dependency dev và khỏi bảng ở [02](../../../docs/architecture/02-backend-structure.md), vì không còn container api để attach.

## Quyết định

Chốt khi grilling ngày 29/10/2026.

| Chủ đề | Quyết định |
|---|---|
| Image | `python:3.14.<vá>-slim`, `uv` chép từ image `ghcr.io/astral-sh/uv:<bản>`, cài bằng `uv sync --locked --no-build --no-dev`. Venv ở `/opt/venv` (ngoài `/app`) để bind mount `backend/` không đè `.venv` của máy lên venv của container. Chạy bằng user không phải root |
| Phiên bản image | Valkey `8.1.11`, trùng service của CI; Mailpit ghim bản vá. 08 mục 7 sửa theo |
| `REDIS_PORT` | Khai báo `REDIS_PORT: int = 6380` trong `config/env.py` như `PG_PORT` (chỉ Compose dùng), vì `Env` có `extra="forbid"` |
| `make db-reset` | Lệnh `shared` `manage.py reset_db`: nối database `postgres`, `DROP DATABASE … WITH (FORCE)`, `CREATE DATABASE … OWNER <user>`; từ chối khi `DEBUG` tắt hoặc host không phải `localhost`/`127.0.0.1`. Recipe: `reset_db` → `$(MAKE) migrate` (`migrate` → `sync_beat_schedule`). Khác *Việc cần làm*: thêm lệnh này vì recipe chỉ được gọi `uv run`/`docker compose` (ADR 0017), không gọi `psql` |
| `make migrate` | Chạy trên máy: `migrate` rồi `sync_beat_schedule` |
| `make restart-worker` | Khởi động lại `worker`, `beat`; ticket 10 thêm `relay` |
| `sync_beat_schedule` | Tên `PeriodicTask` là key của `beat_schedule`. Hỗ trợ lịch crontab và interval; job trong DB đang dùng `solar`/`clocked` được chuyển về lịch của code. Đồng bộ `task`, lịch, `queue`, `enabled`; job trong DB không còn trong code thì `enabled=False`. Mỗi thay đổi ghi một dòng log |
| `celery.backend_cleanup` | Đặt `result_expires = None` trong `config/celery.py` để Beat không tự thêm job này (không có result backend, 07 mục 3.3). Khác *Việc cần làm*: thêm một dòng cấu hình Celery |
| `debugpy` | Bỏ package khỏi nhóm dev và bảng ở 02. Giữ extension VS Code `ms-python.debugpy` và `"type": "debugpy"` trong `launch.json` (debugger của IDE, không phải package) |
| Thêm sau review (29/10) | Giữ `.dockerignore` (không đưa `.env`, `.venv` vào image), chép code vào image (image chạy được khi không bind mount, ticket 14 quét image này; sau SonarCloud đổi sang chép tường minh), `name: fashion` trong Compose (tên container không trùng project khác ở thư mục `backend`); 08 mục 7 sửa theo |
| Transaction trong command | `sync_beat_schedule` giữ `@transaction.atomic` (đồng bộ lịch phải trọn vẹn); 02 §9.1 thêm ngoại lệ cho management command hạ tầng của `shared` |
| SonarCloud PR #27 (30/10) | Compose không ghi `DATABASE_URL` có mật khẩu: `Env.DATABASE_HOST` (mặc định rỗng) thay host của `DATABASE_URL`, container đặt `host.docker.internal`. Dockerfile chép tường minh `manage.py`, `config/`, `shared/`, `modules/` thay cho `COPY . .` |
| Commit `8687733` | Sửa tài liệu ngoài *Việc cần làm* (lệnh JWT, 08 §2.4, §3.1, comment pre-commit, README) giữ trong PR, ghi ngoài phạm vi ở Notes |

## Acceptance criteria

- [x] Trên DB trống, `make up` chạy `migrate` trước rồi mới bật worker, beat; không service nào khởi động lại liên tục. Sau đó `make run`, `curl localhost:8000/healthz` và `/readyz` trả 200.
- [ ] Các lệnh trên chạy được trên Windows (PowerShell 7, GNU make) và macOS.
- [x] `sync_beat_schedule`: DB rỗng thì tạo đủ job theo code; chạy lần hai không đổi gì; job có trong DB nhưng không còn trong code bị tắt, không bị xoá; tần suất trong DB khác code thì được sửa theo code.
- [ ] `make db-reset` xoá và tạo lại database `fashion` rồi migrate.
- [x] Tài liệu nào lệch với cái đã làm (Compose, lệnh Makefile, phiên bản image) được sửa trong cùng PR.

## Comments

### Báo cáo 29/10/2026

**Nhánh:** `chore/docker-compose-local` · **PR:** #27 · **Mode:** full

#### Đã làm

| AC | Bằng chứng |
| --- | --- |
| 1. `make up` trên DB trống: `migrate` chạy trước, worker/beat không restart liên tục; `make run`, `/healthz`, `/readyz` trả 200 | `tests/test_env.py::test_redis_port_is_accepted_and_defaults_to_6380` (phần `REDIS_PORT`). Kiểm tay trên Docker Desktop 29.7.2 bằng `docker compose up -d --build` trên database `fashion` trống: `migrate` Exited(0) sau khi áp mọi migration và chạy `sync_beat_schedule`, worker/beat Up và không restart, container chạy user `app` (uid 999); `runserver` trên máy trả `/healthz` 200, `/readyz` 200 (không test tự động: cần Docker và PostgreSQL thật) |
| 2. Lệnh chạy được trên Windows (PowerShell 7, GNU make) và macOS | Kiểm tay một phần: từng lệnh trong recipe (`docker compose …`, `uv run …`) chạy được trên Windows. Chưa chạy qua GNU make vì máy chưa cài; macOS không có máy để kiểm (không test tự động: phụ thuộc hệ điều hành và shell) |
| 3. `sync_beat_schedule` tạo đủ job, chạy lần hai không đổi gì, tắt job thừa (không xoá), sửa tần suất lệch | `shared/tests/test_sync_beat_schedule.py::test_empty_db_creates_every_job_from_code`, `::test_second_run_changes_nothing`, `::test_job_missing_from_code_is_disabled_not_deleted`, `::test_db_frequency_differing_from_code_is_corrected`, `::test_db_job_on_other_schedule_type_is_switched_to_code_schedule` |
| 4. `make db-reset` xoá, tạo lại database `fashion` rồi migrate | `shared/tests/test_reset_db.py::test_refuses_when_debug_is_off`, `::test_refuses_non_local_database_host` (3 host: tên miền, RDS, rỗng) cho phần chặn an toàn. Kiểm tay phần xoá/tạo thật trên database nháp `fashion_reset_check`: tạo được khi chưa có, owner `fashion`, `DROP … WITH (FORCE)` chạy được khi còn session mở. Chưa chạy `make db-reset` trên `fashion` |
| 5. Tài liệu lệch được sửa trong cùng PR | Rà tay theo danh sách thay đổi; xem *Tài liệu đã cập nhật* |

Lint (`ruff check`, `ruff format --check`, `mypy`, `lint-imports`) xanh · test: 148 passed trong 6.11s (sau vòng sửa review). Hai lệnh chạy thẳng recipe của `make lint` / `make test` vì máy chưa có GNU make.

#### Chưa làm

- Kiểm tay còn thiếu: chạy các lệnh qua GNU make, macOS, `make db-reset` trên database `fashion` khi worker/beat đang chạy, mở thử run config của VS Code và PyCharm.

#### Gap

- `make db-reset` cắt mọi kết nối (`WITH (FORCE)`), Compose không đặt restart policy nên beat có thể thoát; nếu đúng vậy thì tài liệu ghi chạy `make restart-worker` sau `db-reset`.
- `.env` tạo trước ticket này vẫn có `REDIS_URL=redis://redis:6379/0`, `EMAIL_HOST=mailpit`; phải đổi sang `redis://localhost:6380/0` và `localhost` theo `.env.example`.
- Image trong `docker-compose.yml` chưa có ecosystem `docker-compose` trong Dependabot: tách thành ticket [20](./20-dependabot-compose-images.md) (`needs-triage`).
- Ngoài *Việc cần làm*: thêm `.dockerignore` (không đưa `.env`, `.venv` vào image), chép code vào image (image chạy được khi không bind mount, ticket 14 quét image này; sau SonarCloud đổi sang chép tường minh), `name: fashion` trong Compose; ghim image ở bản đã phát hành ≥ 7 ngày: `python:3.14.9-slim`, `ghcr.io/astral-sh/uv:0.13.5`, `valkey/valkey:8.1.11`, `axllent/mailpit:v1.31.6`.
- `django-celery-beat` không có type hints: thêm `django_celery_beat.*` vào override `ignore_missing_imports` của mypy.

#### Thay đổi theo yêu cầu

- 30/10/2026, SonarCloud Blocker `docker-compose.yml:10` (mật khẩu PostgreSQL ghi cứng): thêm `Env.DATABASE_HOST`, `database_config(url, host=…)`; Compose chỉ đặt `DATABASE_HOST: host.docker.internal`. Test: `tests/test_database_url.py::test_host_argument_overrides_host_of_url`, `tests/test_env.py::test_database_host_is_accepted_and_defaults_to_empty`; kiểm tay `docker compose up -d --build`: `migrate` Exited(0), worker/beat Up.
- 30/10/2026, SonarCloud High `Dockerfile:26` (`COPY . .`): chép tường minh `manage.py`, `config/`, `shared/`, `modules/`; kiểm tay `ls /app` trong image chỉ còn các mục đó cùng `pyproject.toml`, `uv.lock`, `.python-version`.
- 30/10/2026, SonarCloud thứ tự assert trong `test_sync_beat_schedule.py`: 6 assert có tuple ở vế trái (Sonar coi là giá trị kỳ vọng) tách thành từng assert `actual == expected`; hành vi test không đổi, 5 test xanh.

- Sửa tài liệu ngoài *Việc cần làm* ở commit `8687733` (lệnh JWT, 08 §2.4, §3.1, comment pre-commit, README): giữ trong PR theo quyết định sau review.

#### Review

Một vòng sửa, xanh.

| Mã | Chỗ | Kết luận | Lý do |
| --- | --- | --- | --- |
| Sp6 | `shared/management/commands/sync_beat_schedule.py:38` | đã sửa | job đang dùng lịch `solar`/`clocked` không sửa được; `wanted` đặt `solar`, `clocked` về `None`, test red trước (2bd6aa4) |
| Sp7 | `.run/Django server.run.xml:3` | đã sửa | bỏ `<module>` ghim tên thư mục clone (27dd344) |
| St4 | `shared/management/commands/sync_beat_schedule.py:27` | đã sửa | `code_schedule` hai nghĩa → `beat_schedule`, `job_schedule`, `_resolve_schedule_row` (051698f) |
| St5 | `backend/Makefile:51` | đã sửa | `db-reset` gọi `$(MAKE) migrate` thay vì lặp lệnh (e046cc3) |
| Sp4, Sp5 | `backend/docker-compose.yml:6`, `backend/Dockerfile:26`, `backend/.dockerignore` | chỉ báo | ngoài *Việc cần làm*, người dùng giữ, ghi vào `## Quyết định` |
| St1 | `shared/management/commands/sync_beat_schedule.py:25` | chỉ báo | transaction trong command; giữ, 02 §9.1 thêm ngoại lệ ở phase sync |
| Sp3 | commit `8687733` | chỉ báo | sửa tài liệu ngoài phạm vi, giữ trong PR |
| Sp1, Sp2 | AC2, AC4 | chỉ báo | chưa chạy qua GNU make, chưa `make db-reset` trên `fashion`; kiểm tay trước G2 |
| St3 | `shared/tests/test_reset_db.py` | chỉ báo | nhánh DROP/CREATE không test tự động (phá huỷ), kiểm tay |
| St2, St6, St7 | test, `.env.example`, `config/env.py` | chỉ báo | smell: chưa có factory cho model `django-celery-beat`; `6380` lặp ở `REDIS_PORT`/`REDIS_URL` như mẫu `PG_PORT`; assert lặp trong test |
| St8 | `backend/Makefile:36` | bác | `s=worker` đúng 08 §3 |

#### Tài liệu đã cập nhật

- `docs/architecture/02-backend-structure.md`: bỏ `debugpy` khỏi bảng dev; cây thư mục: Dockerfile cho worker/beat/relay/migrate, thêm `.dockerignore`, `reset_db.py`, Compose không còn api; §9.1 cho phép transaction trong management command hạ tầng của `shared`.
- `docs/architecture/08-local-development.md`: mục 7 khớp `docker-compose.yml` (`name: fashion`, khối `x-base`, image ghim `valkey/valkey:8.1.11`, `axllent/mailpit:v1.31.6`, mô tả Dockerfile); mục 3 `restart-worker`, `db-reset`; mục 6 thêm extension Python Debugger.
- `docs/architecture/06-integrations.md`: Mailpit local, worker dùng `mailpit:1025`, API trên máy dùng `localhost:1025`.
- `docs/architecture/07-async-events-jobs.md`: nơi chạy `sync_beat_schedule` ở local.
- `docs/architecture/09-deployment-aws-target.md`: image Valkey local và CI là `8.1.11`.
- `.github/dependabot.yml`: bỏ comment "backend/ chưa có".
- `backend/.env.example`: comment nêu cả `postgres.ps1`.
