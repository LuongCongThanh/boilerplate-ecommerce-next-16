# Báo cáo

- Đã tạo `ci.yml` (job `secrets`, `pr-title`, `backend`), `codeql.yml` (`actions`, `python`, bộ `security-extended`) và `dependabot.yml`. Kiểm tra local: `actionlint` sạch, `zizmor` không có finding, `dependabot.yml` đúng schema.
- Chọn bản action phát hành cách đây ít nhất 2 tuần: `setup-uv` v10.3.0 (thay vì v10.3.2 mới 4 ngày), `codeql-action` v4.38.3. Dependabot có `cooldown: 7` ngày cho cùng lý do.
- Job `backend` và CodeQL `python` tự bỏ qua khi chưa có code Python. Mục `uv` và `docker` của Dependabot sẽ báo lỗi cho tới khi có `backend/`.
- Chưa làm job `trivy` vì chưa có `backend/Dockerfile`. Ticket giữ `needs-info` cho tới khi có Dockerfile.
- Ba AC còn lại (CI xanh trên PR, Dependabot nhận 3 hệ sinh thái, CodeQL hiện ở tab Security) chỉ kiểm được sau khi mở PR trên GitHub.
- SonarCloud báo 12 issue `S8541` (thiếu `--no-build`) và `S8544` (không khoá phiên bản) ở các lệnh `uv`. Đã sửa: `uv sync --locked --no-build` một lần, sau đó gọi thẳng công cụ trong `.venv`; backend khai báo `[tool.uv] package = false`. PR #4 xanh toàn bộ, kể cả SonarCloud.
- 29/10/2026: CodeQL đã có kết quả trên GitHub (PR #17, #18, #19). Đóng ticket; job `trivy` và việc xác nhận Dependabot cho `uv`/`docker` chuyển sang [backend-bootstrap/14](../../../backend-bootstrap/issues/14-trivy-and-dependabot-backend/spec.md), `Blocked by: 07`.
