# Spec: M0 – Dựng khung backend

Status: ready-for-agent

## Bối cảnh

Tài liệu `docs/` đã chốt cho MVP nhưng repo chưa có `backend/`. M0 dựng khung Django theo [02](../../docs/architecture/02-backend-structure.md) và phần hạ tầng `shared` mà mọi module sau đều dùng, để M1 bắt đầu viết nghiệp vụ trên một nền đã có CI, test và các cổng chặn. Vị trí của M0 trong toàn bộ MVP: [roadmap](../mvp-roadmap/map.md).

## Phạm vi

- Khung project: `backend/pyproject.toml`, `uv.lock`, `config/`, app `shared` và app `modules` (8 package con rỗng), Dockerfile, Docker Compose, Makefile, `/healthz`, `/readyz`.
- `shared`: BaseModel và `uuid7()`, Money, chuẩn hoá số điện thoại, `pii_hmac`, lỗi chung, các lớp API cơ sở, logging, địa giới hành chính.
- `shared.events`: outbox, delivery, relay, consumer, retry và các lệnh vận hành ([07](../../docs/architecture/07-async-events-jobs.md)).
- `shared.api.idempotency` và bảng `shared_idempotency_key`.
- Model `Account` tối thiểu trong migration đầu tiên của `modules` (bắt buộc vì `AUTH_USER_MODEL`), lệnh `create_staff`.
- Các cổng chặn trong CI: coverage, marker, OpenAPI drift, import-linter (ticket 01–04).

## Quyết định

| Chủ đề | Quyết định |
|---|---|
| Python | 3.14; `shared.models.uuid7()` gọi `uuid.uuid7()` ([ADR 0008](../../docs/adr/0008-uuid-v7-primary-keys.md)) |
| Dependency | Chỉ thêm package mà M0 thực sự dùng. Package của nghiệp vụ (`django-fsm-2`, `django-pghistory`, `argon2-cffi`, `PyJWT`, `google-auth`, `httpx`, `Pillow`, `django-storages`…) thêm ở mốc dùng tới, theo phiên bản ở 02 mục 3 |
| PostgreSQL | Local cài trên máy ([ADR 0015](../../docs/adr/0015-local-postgres-on-host.md)); CI dùng `postgres:18` |
| Account ở M0 | Chỉ field và ràng buộc ở [03 mục 2.1](../../docs/architecture/03-data-model.md#21-identity_account-tài-khoản). Đăng nhập, JWT và các luồng khác của identity thuộc M1 và M6 |
| Tài liệu | Code lệch tài liệu thì sửa tài liệu trong cùng PR |

## Ticket

Thứ tự làm theo số; `Blocked by` ghi ở đầu từng ticket.

1. [`07-project-skeleton.md`](./issues/07-project-skeleton.md): khung project, Compose, Makefile, health check, cấu hình lint.
2. [`08-local-postgres-installer.md`](./issues/08-local-postgres-installer.md): chạy thử bộ cài PostgreSQL trên máy thật (người làm).
3. [`09-shared-core.md`](./issues/09-shared-core.md): BaseModel, Money, phones, privacy, lỗi, API cơ sở, logging, địa giới.
4. [`10-shared-events-outbox.md`](./issues/10-shared-events-outbox.md): outbox, relay, consumer, retry.
5. [`11-shared-idempotency.md`](./issues/11-shared-idempotency.md): `Idempotency-Key`.
6. [`12-account-bootstrap.md`](./issues/12-account-bootstrap.md): model Account và `create_staff`.
7. Cổng chặn CI: [`01`](./issues/01-services-coverage-gate.md) coverage, [`02`](./issues/02-pytest-markers-and-br-report.md) marker, [`03`](./issues/03-openapi-schema-drift-check.md) OpenAPI drift, [`04`](./issues/04-import-linter-test-factories.md) import-linter.

[`05-load-test-k6-staging.md`](./issues/05-load-test-k6-staging.md) không thuộc M0; làm ở M7.

## Ngoài phạm vi

- Mọi model nghiệp vụ ngoài Account, mọi endpoint ngoài `/healthz`, `/readyz` và địa giới hành chính.
- Hạ tầng AWS ([09](../../docs/architecture/09-deployment-aws-target.md)).
