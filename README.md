# Fashion Store – Backend Django

Website bán lẻ thời trang B2C cho thị trường Việt Nam. Backend là **Django + Django REST Framework** (modular monolith), phục vụ storefront và back-office Next.js (làm sau).

> Trạng thái: **giai đoạn tài liệu**. Repo hiện chỉ chứa tài liệu; code Backend sẽ được khởi tạo theo [cấu trúc đã thiết kế](./docs/architecture/02-backend-structure.md).

## Tóm tắt

| Hạng mục | Lựa chọn |
|---|---|
| Mô hình | B2C, một người bán, thời trang (Biến thể size × màu) |
| Thanh toán | VNPay, MoMo, COD |
| Vận chuyển | GHN |
| Backend | Python 3.13, Django 5.2 LTS, DRF, PostgreSQL 18, Redis, Celery |
| Kiến trúc | Modular monolith: app `modules` với 8 module con, app `shared` hạ tầng |
| Local | PostgreSQL cài trên máy; API, Celery, Redis, Mailpit chạy bằng Docker Compose |
| Production (mục tiêu) | AWS Singapore: ECS Fargate, RDS, ElastiCache, S3, SES |

## Tài liệu

Thuật ngữ chung: **[GLOSSARY.md](./GLOSSARY.md)** — đọc trước tiên.

### Business (`docs/business/`)

1. [Tầm nhìn và phạm vi](./docs/business/01-vision-scope.md)
2. [Vai trò người dùng và phân quyền](./docs/business/02-actors-permissions.md)
3. [User stories](./docs/business/03-user-stories.md)
4. [Quy tắc nghiệp vụ](./docs/business/04-business-rules.md)
5. [Vòng đời Đơn hàng](./docs/business/05-order-lifecycle.md)
6. [Tuân thủ pháp lý](./docs/business/06-compliance.md)

### Architecture (`docs/architecture/`)

1. [Bối cảnh hệ thống (C4)](./docs/architecture/01-system-context.md)
2. [Cấu trúc Backend: thư mục, công nghệ, package, vai trò từng file](./docs/architecture/02-backend-structure.md) ⭐
3. [Mô hình dữ liệu](./docs/architecture/03-data-model.md)
4. [API contract](./docs/architecture/04-api-contract.md)
5. [Xác thực và bảo mật](./docs/architecture/05-auth-security.md)
6. [Tích hợp bên ngoài](./docs/architecture/06-integrations.md)
7. [Sự kiện và job chạy nền](./docs/architecture/07-async-events-jobs.md)
8. [Môi trường phát triển local](./docs/architecture/08-local-development.md)
9. [Triển khai AWS (mục tiêu)](./docs/architecture/09-deployment-aws-target.md)
10. [Yêu cầu phi chức năng](./docs/architecture/10-nfr.md)
11. [Quy ước Git](./docs/architecture/11-git-workflow.md)
12. [Chiến lược test](./docs/architecture/12-testing-strategy.md)

### Quyết định kiến trúc (`docs/adr/`)

| ADR | Quyết định |
|---|---|
| [0001](./docs/adr/0001-nextjs-frontend-django-api.md) | Frontend Next.js tách riêng, Backend là Django API |
| [0002](./docs/adr/0002-auth-nextauth-session-django-jwt.md) | NextAuth giữ session, Django tự phát hành JWT bằng PyJWT |
| [0003](./docs/adr/0003-postgres-redis-celery.md) | PostgreSQL, Redis và Celery làm runtime |
| [0004](./docs/adr/0004-custom-nextjs-admin.md) | Back-office tự xây bằng Next.js thay vì Django Admin |
| [0005](./docs/adr/0005-provider-adapters-fake-gateways.md) | Adapter cho nhà cung cấp, cổng giả lập và job đối soát |
| [0006](./docs/adr/0006-modular-monolith.md) | Modular monolith: một app `modules` chia module con |
| [0007](./docs/adr/0007-events-outbox-celery-no-kafka.md) | Sự kiện qua Outbox + Celery, chưa dùng Kafka |
| [0008](./docs/adr/0008-uuid-v7-primary-keys.md) | Khoá chính UUID v7, sinh bằng `uuid-utils` |

### Cấu hình cho agent (`docs/agents/`)

Quy ước để Claude Code và các skill engineering đọc repo này. Điểm vào là [CLAUDE.md](./CLAUDE.md).

1. [Issue tracker](./docs/agents/issue-tracker.md): spec và ticket dạng Markdown trong `.scratch/`, cách đóng ticket
2. [Trạng thái triage](./docs/agents/triage-labels.md)
3. [Tài liệu domain](./docs/agents/domain.md): agent đọc GLOSSARY, ADR và quy tắc nghiệp vụ thế nào

### Tài liệu Frontend cũ

Bộ tài liệu Next.js cũ (`docs/README.md`, `ARCHITECTURE.md`, `DOCS_INDEX.md`, `MIGRATION.md`, `PERFORMANCE.md`, `IMPORT_ALIAS_GUIDE.md`, `MCP_GUIDE.md`) đã được xoá vì không còn khớp với các quyết định trên. Khi làm Frontend có thể xem lại trong lịch sử git (commit `0f83e4c`).
