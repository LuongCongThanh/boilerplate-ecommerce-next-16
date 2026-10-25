# Cấu hình bảo mật GitHub và `SECURITY.md`

Status: ready-for-human

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

- [ ] `SECURITY.md` hiện ở tab Security → Policy.
- [ ] Push thử một secret giả lên một nhánh nháp thì bị Push Protection chặn.
- [ ] Push thẳng lên `main` bị từ chối.
- [ ] Nút "Report a vulnerability" hiện trong tab Security.

## Comments
