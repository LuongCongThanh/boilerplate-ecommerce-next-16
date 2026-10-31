# CI workflow, CodeQL, Dependabot và trivy

Status: resolved

Spec: [spec.md](../../spec.md)

**PR:** #4

## Việc cần làm

- Tạo `.github/workflows/ci.yml`:
  - Trigger: `push` lên `main`/`dev` và `pull_request`. **Không** dùng `pull_request_target`.
  - `permissions: contents: read` ở cấp workflow.
  - Job `secrets`: chạy `gitleaks` trên toàn bộ lịch sử (`fetch-depth: 0`).
  - Job `backend`: lint (`ruff check`, `ruff format --check`, `mypy`, `lint-imports`), test, `pip-audit`. Chỉ chạy khi có `backend/pyproject.toml`; nếu chưa có thì bỏ qua và báo rõ trong log.
  - Job `pr-title`: kiểm tra tiêu đề PR theo Conventional Commits (`11-git-workflow.md`).
  - Đặt tên job ổn định, vì ruleset ở ticket 03 sẽ bắt buộc các check này.
- Tạo `.github/workflows/codeql.yml` cho `python` và `actions`, chạy trên PR, push lên `main` và hằng tuần. Chỉ job này được thêm `security-events: write`.
- Tạo `.github/dependabot.yml` cho `uv` (thư mục `/backend`), `github-actions` (`/`), `docker` (`/backend`). Chạy hằng tuần, gom minor và patch thành một PR cho mỗi hệ sinh thái.
- Pin mọi action bên thứ ba theo commit SHA, kèm comment phiên bản (`# v5.0.0`).
- Job `trivy`: build image backend và quét, fail khi có lỗ hổng `CRITICAL`/`HIGH` đã có bản vá (`ignore-unfixed: true`). **Chỉ thêm khi đã có `backend/Dockerfile`**. Nếu ticket này được làm trước khi có Dockerfile thì ghi lại phần này vào `## Comments` và để ticket mở với `Status: needs-info`.
- Cập nhật `docs/architecture/11-git-workflow.md` để ghi tên các workflow và check bắt buộc.

## Acceptance criteria

- [x] Workflow chạy xanh trên một PR thử vào `dev`.
- [x] Không workflow nào dùng `pull_request_target`; quyền mặc định là `contents: read`.
- [x] Mọi `uses:` của action bên thứ ba đều là SHA 40 ký tự.
- [x] Dependabot nhận đủ 3 hệ sinh thái (xem tab Insights → Dependency graph → Dependabot). Chuyển sang [backend-bootstrap/14](../../../backend-bootstrap/issues/14-trivy-and-dependabot-backend/spec.md) vì `uv` và `docker` cần `backend/`.
- [x] CodeQL hiện kết quả trong tab Security.
- [x] Có job trivy, hoặc có comment ghi lý do hoãn.
