# Dependabot theo dõi image trong `backend/docker-compose.yml`

Status: needs-triage

Blocked by: 15

Spec: [spec.md](../spec.md)

Tách từ ticket [15](./15-docker-compose-local.md) khi review ngày 29/10/2026.

## Bối cảnh

Ticket 15 ghim image của Compose tới bản vá (`valkey/valkey:8.1.11`, `axllent/mailpit:v1.31.6`). `.github/dependabot.yml` chỉ có hệ sinh thái `docker` cho `/backend`, hệ này đọc `Dockerfile`, không đọc `docker-compose.yml`, nên hai image trên không được đề xuất cập nhật. Ticket [14](./14-trivy-and-dependabot-backend.md) chỉ kiểm tra 3 hệ sinh thái `uv`, `docker`, `github-actions`.

## Việc cần làm

- Thêm hệ sinh thái `docker-compose` cho `/backend` vào `dependabot.yml`, cùng `cooldown` 7 ngày và cách gom PR như các mục khác.
- Valkey của Compose phải cùng bản với service của CI (`.github/workflows/ci.yml`): quyết định cách giữ hai chỗ cùng bản khi Dependabot chỉ sửa một chỗ.

## Acceptance criteria

- [ ] Dependabot nhận hệ sinh thái `docker-compose` và không báo lỗi.
- [ ] Có cách giữ bản Valkey của Compose và CI trùng nhau, ghi trong 08 mục 7.
