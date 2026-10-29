# Docker Compose local, lệnh Makefile dùng container và `sync_beat_schedule`

Status: ready-for-agent

Spec: [spec.md](../spec.md)

Blocked by: 07, 08

## Bối cảnh

Tách từ ticket [07](./07-project-skeleton.md) để phần cần container gọi được PostgreSQL trên máy (ticket [08](./08-local-postgres-installer.md)) nằm riêng một chỗ, không chặn phần còn lại của khung project.

`sync_beat_schedule` nằm ở đây vì service `migrate` và `make migrate` gọi nó ([08 mục 7](../../../docs/architecture/08-local-development.md#7-docker-composeyml-rút-gọn)). Lệnh chỉ đồng bộ lịch Celery Beat, không phụ thuộc outbox. Service `relay` thêm vào Compose ở ticket [10](./10-shared-events-outbox.md), cùng lúc với lệnh `run_outbox_relay`.

## Việc cần làm

- `Dockerfile` một image cho api, worker, beat, relay (cài bằng `uv sync --locked --no-build`).
- `docker-compose.yml` gồm migrate, api, worker, beat, redis (Valkey 8), mailpit theo 08 mục 7: service `migrate` chạy `migrate` và `sync_beat_schedule` rồi thoát, các service app chờ nó thoát thành công; không có service postgres; pin image tới bản vá.
- `shared/management/commands/sync_beat_schedule.py`: ghi lịch job từ `config/celery.py` vào `django-celery-beat`, tắt job thừa ([07 mục 3.2](../../../docs/architecture/07-async-events-jobs.md)).
- Thêm vào `Makefile` các lệnh dùng container ở [08 mục 3](../../../docs/architecture/08-local-development.md#3-lệnh-hằng-ngày-makefile): `up`, `down`, `logs`, `shell`, `makemigrations`, `migrate`, `db-reset`.

## Acceptance criteria

- [ ] Trên DB trống, `make up` chạy `migrate` trước rồi mới bật api, worker, beat; không service nào khởi động lại liên tục. `curl localhost:8000/healthz` và `/readyz` trả 200.
- [ ] `sync_beat_schedule`: DB rỗng thì tạo đủ job theo code; chạy lần hai không đổi gì; job có trong DB nhưng không còn trong code bị tắt, không bị xoá; tần suất trong DB khác code thì được sửa theo code.
- [ ] `make db-reset` xoá và tạo lại database `fashion` rồi migrate.
- [ ] Tài liệu nào lệch với cái đã làm (Compose, lệnh Makefile, phiên bản image) được sửa trong cùng PR.
