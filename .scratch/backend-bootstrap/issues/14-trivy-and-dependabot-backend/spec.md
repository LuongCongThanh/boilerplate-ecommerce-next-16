# Quét image bằng trivy và xác nhận Dependabot cho `backend/`

Status: ready-for-agent

Spec: [spec.md](../../spec.md)

Blocked by: 15

## Bối cảnh

Tách từ [dev-security-baseline/02](../../../dev-security-baseline/issues/02-ci-and-dependabot/spec.md): hai phần đó phải có `backend/` mới làm được. `dependabot.yml` đã khai báo hệ sinh thái `uv` và `docker` cho `/backend`, nhưng chúng sẽ báo lỗi cho tới khi có `backend/pyproject.toml` và `backend/Dockerfile` (ticket 07 và [15](../15-docker-compose-local/spec.md)).

## Việc cần làm

- Thêm job `trivy` vào `.github/workflows/ci.yml`: build image từ `backend/Dockerfile` rồi quét, fail khi có lỗ hổng `CRITICAL`/`HIGH` đã có bản vá (`ignore-unfixed: true`). Pin action theo commit SHA kèm comment phiên bản, giống các action khác.
- Đặt tên job ổn định, rồi thêm `trivy` vào required status checks của ruleset `main` (id 25858832). Agent chỉ chạy lệnh `gh` đổi ruleset sau khi chủ repo xác nhận.
- Ghi tên job `trivy` vào danh sách check bắt buộc ở `docs/architecture/11-git-workflow.md`.
- Sau khi 15 vào `dev`, kiểm tra Dependabot nhận đủ 3 hệ sinh thái `uv`, `docker`, `github-actions`.

## Acceptance criteria

- [ ] Job `trivy` chạy xanh trên PR có `backend/Dockerfile`.
- [ ] `trivy` nằm trong required status checks của ruleset `main`.
- [ ] Dependabot nhận đủ 3 hệ sinh thái (tab Insights → Dependency graph → Dependabot), không còn lỗi ở `uv` và `docker`.
