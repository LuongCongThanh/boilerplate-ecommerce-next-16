# Bộ cài PostgreSQL local cho Windows (`postgres.ps1`, không dùng WSL2)

Status: resolved

Spec: [spec.md](../spec.md)

## Bối cảnh

Theo [ADR 0017](../../../docs/adr/0017-windows-native-dev-api-on-host.md), Windows dev thẳng trên Windows, không qua WSL2. PostgreSQL cài tay một lần bằng bộ cài EDB hoặc `winget install PostgreSQL.PostgreSQL.<major>`; script `scripts/setup/postgres.ps1` lo phần chạy lại được: role, database, kiểm tra extension. `scripts/setup/postgres.sh` chỉ còn dùng cho macOS và Ubuntu (ticket [13](./13-local-postgres-installer-macos.md)).

Ticket này chặn ticket [15](./15-docker-compose-local.md) (Docker Compose): container phải gọi được PostgreSQL trên máy.

## Đã làm tay trên máy đầu tiên (2026-10-29)

- PostgreSQL 18 cài bằng bộ cài EDB, chạy thành service `postgresql-x64-18`, cổng 5432; pgAdmin 4 cài kèm.
- Role và database tạo bằng `psql` với user `postgres`, tương đương chạy trong Query Tool của pgAdmin:
  ```sql
  CREATE ROLE fashion LOGIN CREATEDB PASSWORD 'fashion';
  CREATE DATABASE fashion OWNER fashion;
  ```
- Kết quả kiểm tra:
  - `psql postgres://fashion:fashion@localhost:5432/fashion` vào được (`PostgreSQL 18.6 on x86_64-windows`).
  - `unaccent`, `pg_trgm`, `btree_gist` có trong `pg_available_extensions`.
  - `docker run --rm postgres:18 psql postgres://fashion:fashion@host.docker.internal:5432/fashion` vào được. `inet_client_addr()` trả `127.0.0.1`, nên `pg_hba.conf` mặc định của EDB đủ dùng, không phải sửa `listen_addresses` hay `pg_hba.conf`.
- Máy có Memurai (Redis cho Windows) giữ cổng 6379, nên Redis của Compose dùng `REDIS_PORT=6380` ([08 mục 1](../../../docs/architecture/08-local-development.md#1-tổng-quan)).

## Script làm gì

- Kiểm tra `git`, `make`, `docker`, `uv ≥ 0.13`: chỉ báo thiếu, không tự cài.
- Tìm service `postgresql-x64-*` có major cao nhất. Chưa có thì in lệnh `winget install PostgreSQL.PostgreSQL.<major>` (major mới nhất) rồi dừng. Service đang tắt thì báo và dừng.
- Đọc cổng của cluster đó (`postgresql.conf` trong data directory hoặc `SHOW port`), không tự chọn cổng.
- Hỏi mật khẩu `postgres` bằng `Read-Host -AsSecureString`; nếu đã có `PGPASSWORD` trong môi trường thì dùng luôn. Không lưu mật khẩu ra đâu cả.
- Tạo hoặc cập nhật role `fashion`/`fashion` (`LOGIN CREATEDB`) và database `fashion` do `fashion` sở hữu.
- Kiểm tra `unaccent`, `pg_trgm`, `btree_gist` có trong `pg_available_extensions` (migration mới là bên tạo extension).
- Thử đăng nhập bằng `fashion` qua TCP, rồi in `DATABASE_URL` và `PG_PORT` để chép vào `backend/.env`.

## Việc cần làm

- Viết `scripts/setup/postgres.ps1` (CRLF theo `.gitattributes`, chạy được bằng PowerShell 7).
- Sửa `scripts/setup/postgres.sh`: bỏ nhánh WSL và lời nhắc `networkingMode=mirrored`; gặp Windows thì chỉ sang `postgres.ps1`.
- `.vscode/launch.json`: "Pytest (local)" đang trỏ `.venv/bin/python`, trên Windows là `.venv/Scripts/python.exe`; sửa để chạy được cả hai hệ điều hành.

## Acceptance criteria

- [x] Script chạy xong trên Windows 11, chạy lần thứ hai không lỗi và không đổi gì (2026-10-29, PostgreSQL 18.6, cổng 5432). Sai mật khẩu `postgres` thì dừng với exit 1 và báo rõ.
- [x] Máy chưa cài PostgreSQL: script in lệnh winget và dừng, không làm gì khác. Chưa thử trên máy thật chưa cài; đã kiểm riêng phần tìm major mới nhất trên winget (trả `18`).
- [x] `psql postgres://fashion:fashion@localhost:<PG_PORT>/fashion` vào được (đã kiểm tay, 2026-10-29).
- [x] Từ một container (`docker run --rm postgres:18 psql postgres://fashion:fashion@host.docker.internal:<PG_PORT>/fashion -c 'select 1'`) vào được (đã kiểm tay, 2026-10-29).
- [x] Mật khẩu `postgres` không xuất hiện trong output, log hay file nào: nhập ẩn hoặc lấy từ `PGPASSWORD`, chỉ đặt vào `PGPASSWORD` trong lúc gọi `psql` rồi trả lại giá trị cũ.
- [x] `08` không còn nhãn **[Cần xác minh]** về kết nối PostgreSQL trên Windows.
