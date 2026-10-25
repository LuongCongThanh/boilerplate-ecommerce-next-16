# pre-commit, ruff `S` và chặn agent đọc secret

Status: resolved

Spec: [spec.md](../spec.md)

## Việc cần làm

- Tạo `.pre-commit-config.yaml` ở gốc repo, gồm:
  - `gitleaks` (hook chính thức của `gitleaks/gitleaks`).
  - `pre-commit-hooks`: `detect-private-key`, `check-added-large-files`, `check-yaml`, `check-toml`, `end-of-file-fixer`, `trailing-whitespace`.
  - `ruff` (check + format) và hook `commit-msg` của `commitizen` như `11-git-workflow.md` đã mô tả.
  - Pin `rev` theo phiên bản cụ thể.
- Cập nhật cấu hình ruff mẫu trong `docs/architecture/02-backend-structure.md`:
  - Thêm `"S"` vào `select`.
  - Thêm `[tool.ruff.lint.per-file-ignores]` với `"tests/**" = ["S101", "S105", "S106"]`.
- Cập nhật `docs/architecture/11-git-workflow.md` mục 8: ghi `gitleaks` bên cạnh `detect-private-key`, và quy tắc dữ liệu mẫu trong test phải là giá trị giả rõ ràng.
- Thêm vào `.claude/settings.json` (giữ nguyên phần `attribution` đang có):

  ```json
  "permissions": {
    "deny": [
      "Read(./.env)",
      "Read(./.env.*)",
      "Read(./**/.env)",
      "Read(./**/.env.*)",
      "Read(./.secrets/**)",
      "Read(./**/.secrets/**)",
      "Read(./**/*.pem)"
    ],
    "allow": ["Read(./**/.env.example)"]
  }
  ```

  Kiểm tra lại cú pháp với tài liệu chính thức của Claude Code. Nếu `deny` thắng `allow` thì đổi cách viết để `.env.example` vẫn đọc được.
- Thêm mục "Bảo mật khi dùng AI agent" vào `CONTRIBUTING.md`: không dán secret vào prompt, không tắt rule deny.

## Acceptance criteria

- [x] `pre-commit run --all-files` chạy xanh trên repo hiện tại.
- [x] Commit thử một file chứa chuỗi giống secret VNPay (ví dụ `vnp_HashSecret=ABCDEFGHIJKLMNOPQRSTUVWXYZ012345`) thì bị `gitleaks` chặn. Không commit file thử này.
- [x] Claude Code bị từ chối khi đọc `.env` và `.secrets/jwt_ed25519.pem`, vẫn đọc được `.env.example`.
- [x] Cấu hình ruff mẫu trong tài liệu có `"S"` và ngoại lệ cho test.

## Comments
- Rule deny dùng cú pháp negation `Read(!.env.example)` thay cho `allow`, vì trong Claude Code `deny` luôn thắng `allow` (https://code.claude.com/docs/en/permissions.md). Rule chỉ áp dụng từ thư mục đang mở trở xuống, nên phải mở Claude Code từ gốc repo; đã ghi vào `CONTRIBUTING.md`.
- Đã kiểm tra bằng `claude -p` mở từ gốc repo với file giả: `.env` và `.secrets/jwt_ed25519.pem` bị từ chối, `.env.example` đọc được.
- Đã kiểm tra `gitleaks` trong một repo tạm: chặn 2 chuỗi giống secret VNPay/MoMo (rule `generic-api-key`).
- Rule deny không chặn script tự đọc file. Nếu cần chặn ở mức hệ điều hành thì bật `sandbox` của Claude Code, để một ticket sau.
