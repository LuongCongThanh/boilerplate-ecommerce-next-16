# Báo cáo

- Rule deny dùng cú pháp negation `Read(!.env.example)` thay cho `allow`, vì trong Claude Code `deny` luôn thắng `allow` (https://code.claude.com/docs/en/permissions.md). Rule chỉ áp dụng từ thư mục đang mở trở xuống, nên phải mở Claude Code từ gốc repo; đã ghi vào `CONTRIBUTING.md`.
- Đã kiểm tra bằng `claude -p` mở từ gốc repo với file giả: `.env` và `.secrets/jwt_ed25519.pem` bị từ chối, `.env.example` đọc được.
- Đã kiểm tra `gitleaks` trong một repo tạm: chặn 2 chuỗi giống secret VNPay/MoMo (rule `generic-api-key`).
- Rule deny không chặn script tự đọc file. Nếu cần chặn ở mức hệ điều hành thì bật `sandbox` của Claude Code, để một ticket sau.
