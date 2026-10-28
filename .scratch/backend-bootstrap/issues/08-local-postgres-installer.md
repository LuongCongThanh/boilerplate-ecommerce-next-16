# Bộ cài PostgreSQL local cho Windows (WSL2) và macOS

Status: ready-for-agent

## Bối cảnh

Theo [ADR 0019](../../../docs/adr/0019-local-postgres-on-host.md), PostgreSQL ở local cài trên máy, bản major mới nhất: Windows cài trong WSL2 Ubuntu bằng apt (PGDG), macOS cài bằng Homebrew. Script `scripts/setup/postgres.sh` đã được viết nhưng **chưa chạy thử trên máy thật**. Ticket này chạy thử, sửa lỗi và gỡ các nhãn **[Cần xác minh]** trong [08](../../../docs/architecture/08-local-development.md).

## Script làm gì

- Nhận hệ điều hành: macOS hoặc Ubuntu/Debian (kể cả WSL2). Hệ khác thì dừng.
- Kiểm tra `git`, `make`, `docker`, `uv ≥ 0.13`: chỉ báo thiếu, không tự cài.
- Tìm bản major mới nhất trên PGDG hoặc Homebrew. Máy đã có bản đó thì dùng luôn; chưa có thì cài thêm, không đụng tới cluster cũ. Nếu cổng 5432 đang bận thì cluster mới chạy ở cổng trống kế tiếp.
- Tạo hoặc cập nhật role `fashion`/`fashion` (`LOGIN CREATEDB`) và database `fashion`.
- Kiểm tra `unaccent`, `pg_trgm`, `btree_gist` có trong `pg_available_extensions` (migration mới là bên tạo extension).
- Thử đăng nhập bằng `fashion` qua TCP; trên WSL thì nhắc bật `networkingMode=mirrored` nếu chưa bật.
- In `DATABASE_URL` và `PG_PORT` để chép vào `backend/.env`.

## Việc cần làm

- Chạy script trên một máy Windows 11 (WSL2 Ubuntu-24.04 mới cài) và một máy macOS (Apple Silicon), mỗi máy hai lần để chắc chạy lại vẫn an toàn.
- Thử trường hợp đã có cluster bản cũ giữ cổng 5432.
- Xác minh container trong Docker Desktop gọi được `host.docker.internal:<PG_PORT>` khi có `networkingMode=mirrored` (Windows) và trên macOS. Nếu không được thì ghi cách sửa (`listen_addresses`, `pg_hba.conf`) vào `08` mục 2.2 và cập nhật script.
- Gỡ nhãn **[Cần xác minh]** tương ứng trong `08`.

## Acceptance criteria

- [ ] Script chạy xong trên Windows (WSL2) và macOS, chạy lần thứ hai không lỗi và không đổi gì.
- [ ] Máy có sẵn cluster cũ ở 5432: cluster cũ giữ nguyên, cluster mới chạy ở cổng khác, `DATABASE_URL` in ra đúng cổng.
- [ ] Từ WSL hoặc macOS: `psql postgres://fashion:fashion@localhost:<PG_PORT>/fashion` vào được.
- [ ] Từ một container (`docker run --rm postgres psql postgres://fashion:fashion@host.docker.internal:<PG_PORT>/fashion -c 'select 1'`) vào được.
- [ ] `08` không còn nhãn **[Cần xác minh]** về kết nối PostgreSQL.
