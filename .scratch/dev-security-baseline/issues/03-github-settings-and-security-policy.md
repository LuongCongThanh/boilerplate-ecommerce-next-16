# Cấu hình bảo mật GitHub và `SECURITY.md`

Status: resolved

Spec: [spec.md](../spec.md)

Blocked by: 02

Ticket này thay đổi cấu hình repo trên GitHub. Agent chỉ được chạy lệnh `gh` sau khi chủ repo xác nhận.

## Việc cần làm

- Tạo `SECURITY.md` ở gốc repo (tiếng Việt):
  - Báo lỗ hổng qua GitHub Private Vulnerability Reporting, **không** mở issue công khai.
  - Thời gian phản hồi dự kiến.
  - Phạm vi: repo này; nhắc rằng đây là boilerplate, không có hệ thống production công khai.
- Trong Settings → Code security, bật:
  - Secret Scanning và Push Protection.
  - Private Vulnerability Reporting.
  - Dependabot alerts và security updates.
- Settings → Actions → General:
  - "Require approval for all outside collaborators" cho workflow từ fork.
  - Workflow permissions: "Read repository contents".
- Tạo ruleset cho `main`:
  - Bắt buộc qua PR, **0 người duyệt** (tạm thời, xem spec).
  - Bắt buộc các status check của ticket 02 và CodeQL.
  - Nhánh phải cập nhật với `main` trước khi merge.
  - Cấm force-push, cấm xoá nhánh.
- Thêm vào `docs/architecture/11-git-workflow.md` mục 6 một ghi chú: đang để 0 người duyệt, nâng lên 1 khi có người thứ hai.

## Acceptance criteria

- [x] `SECURITY.md` hiện ở tab Security → Policy.
- [ ] Push thử một secret giả lên một nhánh nháp thì bị Push Protection chặn.
- [ ] Push thẳng lên `main` bị từ chối.
- [x] Nút "Report a vulnerability" hiện trong tab Security.

## Comments

- Chủ repo đã xác nhận áp dụng toàn bộ. Đã bật qua `gh api` và đọc lại để kiểm tra: Secret Scanning, Push Protection, Dependabot security updates, Private Vulnerability Reporting (`enabled: true`); duyệt workflow từ fork đổi từ `first_time_contributors` sang `all_external_contributors`. Workflow permissions đã là `read` và Dependabot alerts đã bật từ trước.
- Ruleset `main` (id 25858832): `deletion`, `non_fast_forward`, `pull_request` (0 người duyệt, merge hoặc squash), `required_status_checks` (`secrets`, `pr-title`, `backend`, `codeql (actions)`, `codeql (python)`, strict). Không có bypass.
- Chưa thử thật hai AC: push secret giả bị chặn và push thẳng lên `main` bị từ chối. Push Protection chỉ chặn secret đúng định dạng của nhà cung cấp, và thử push lên `main` mà ruleset không chặn thì không gỡ được vì đã cấm force-push. Cấu hình đã đọc lại qua API (`/rules/branches/main`).
- `dev` chưa có ruleset (ngoài phạm vi ticket).
