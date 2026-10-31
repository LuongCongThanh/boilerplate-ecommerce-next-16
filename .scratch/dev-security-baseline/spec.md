# Spec: Nền tảng bảo mật cho quy trình phát triển

Status: ready-for-agent

## Bối cảnh

Repo là public trên GitHub (license MIT) và hiện mới có tài liệu, chưa có code `backend/`. Các biện pháp bảo mật cho quy trình dev (secret, phân tích tĩnh, CI, dependency, công cụ AI) mới chỉ được mô tả trong `docs/architecture/02-backend-structure.md` và `docs/architecture/11-git-workflow.md`, chưa có file cấu hình nào. Repo public nên chỉ một lần commit nhầm secret là secret bị lộ ngay.

Mục tiêu: dựng các hàng rào bảo mật **trước khi** bắt đầu viết code, để code đầu tiên đã chạy qua đầy đủ kiểm tra.

## Phạm vi

Chỉ gồm quy trình phát triển. Quy tắc viết code an toàn trong Django (ORM, serializer, permission…) đã có trong `docs/architecture/05-auth-security.md` và sẽ được rà lại khi bắt đầu viết `backend/`.

## Quyết định

| Chủ đề | Quyết định |
|---|---|
| Visibility | Giữ repo **public**. Không đưa dữ liệu thật (khách hàng, đơn hàng, secret) vào repo, kể cả trong test và fixture |
| Quét secret | `gitleaks` trong `pre-commit` và CI, giữ `detect-private-key`. Bật GitHub Secret Scanning và Push Protection |
| Phân tích tĩnh | Bật nhóm rule `"S"` (flake8-bandit) của ruff. Bật CodeQL cho Python |
| Ngoại lệ trong test | Chỉ trong `backend/tests/**` được bỏ qua `S101`, `S105`, `S106`. Dữ liệu mẫu VNPay/MoMo dùng giá trị giả rõ ràng (ví dụ `test-hash-secret`). Không dùng allowlist rộng cho gitleaks |
| Claude Code | `.claude/settings.json` có rule `deny` để agent không đọc được `.env*`, `.secrets/**`, `*.pem`; cho phép đọc `.env.example`. File được commit cho cả team |
| Dependency | Dependabot cho `uv`, `github-actions`, `docker`, chạy hằng tuần, gom bản minor và patch thành một PR. Giữ `pip-audit` trong CI |
| Image Docker | `trivy` quét image backend trong CI, chặn merge khi có lỗ hổng `CRITICAL`/`HIGH` đã có bản vá. Chỉ làm khi đã có Dockerfile |
| CI với PR từ fork | Chỉ dùng trigger `pull_request`, cấm `pull_request_target`. Bắt buộc duyệt trước khi chạy Actions cho mọi người ngoài. Mọi workflow khai báo `permissions: contents: read`, job nào cần thêm quyền thì tự mở |
| Pin action | Action bên thứ ba được pin theo commit SHA, kèm comment tên phiên bản. Dependabot cập nhật SHA |
| Báo lỗ hổng | `SECURITY.md` bằng tiếng Việt + bật GitHub Private Vulnerability Reporting |
| Bảo vệ `main` | Ruleset: bắt buộc qua PR, CI xanh, cấm push thẳng, cấm force-push, cấm xoá nhánh. **Tạm để 0 người duyệt** cho tới khi có người thứ hai, sau đó nâng lên 1 như `11-git-workflow.md` mục 6 |

## Ticket

1. [`01-pre-commit-and-agent-guard/`](./issues/01-pre-commit-and-agent-guard/spec.md): `pre-commit`, ruff `S`, rule deny cho Claude Code.
2. [`02-ci-and-dependabot/`](./issues/02-ci-and-dependabot/spec.md): CI workflow, CodeQL, Dependabot, trivy.
3. [`03-github-settings-and-security-policy/`](./issues/03-github-settings-and-security-policy/spec.md): cấu hình GitHub và `SECURITY.md`.

## Ngoài phạm vi

- Semgrep (CodeQL là đủ cho giai đoạn này).
- Các quyết định bảo mật của sản phẩm (MFA back-office, mã đơn ngẫu nhiên, xác thực webhook GHN…). Các điểm này vẫn còn mở, sẽ làm thành một feature riêng.
