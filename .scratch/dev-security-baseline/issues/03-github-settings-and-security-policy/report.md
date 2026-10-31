# Báo cáo

- Chủ repo đã xác nhận áp dụng toàn bộ. Đã bật qua `gh api` và đọc lại để kiểm tra: Secret Scanning, Push Protection, Dependabot security updates, Private Vulnerability Reporting (`enabled: true`); duyệt workflow từ fork đổi từ `first_time_contributors` sang `all_external_contributors`. Workflow permissions đã là `read` và Dependabot alerts đã bật từ trước.
- Ruleset `main` (id 25858832): `deletion`, `non_fast_forward`, `pull_request` (0 người duyệt, merge hoặc squash), `required_status_checks` (`secrets`, `pr-title`, `backend`, `codeql (actions)`, `codeql (python)`, strict). Không có bypass.
- Chưa thử thật hai AC: push secret giả bị chặn và push thẳng lên `main` bị từ chối. Push Protection chỉ chặn secret đúng định dạng của nhà cung cấp, và thử push lên `main` mà ruleset không chặn thì không gỡ được vì đã cấm force-push. Cấu hình đã đọc lại qua API (`/rules/branches/main`).
- `dev` chưa có ruleset (ngoài phạm vi ticket).
- Còn lại cho người làm: kiểm tra tab Security → Policy sau khi `SECURITY.md` vào `main`; tự thử Push Protection và push thẳng lên `main` nếu muốn xác nhận thực tế.
- 29/10/2026: Bỏ `Blocked by: 02` vì 02 đã đóng. Chủ repo tự kiểm tra 3 AC còn lại rồi đóng ticket.
