# Bộ cài PostgreSQL local cho macOS

Status: ready-for-human

Spec: [spec.md](../spec.md)

## Bối cảnh

Tách từ ticket [08](./08-local-postgres-installer.md): phần Windows (WSL2) làm ở 08, phần macOS làm ở đây khi team có người dùng Mac. Ticket này **không chặn M0**; trước khi xong, hướng dẫn macOS trong [08](../../../docs/architecture/08-local-development.md) vẫn mang nhãn **[Cần xác minh]**.

Script làm gì: xem ticket 08.

## Việc cần làm

- Chạy `scripts/setup/postgres.sh` trên một máy macOS (Apple Silicon) có Homebrew, hai lần để chắc chạy lại vẫn an toàn.
- Thử trường hợp đã có cluster bản cũ giữ cổng 5432.
- Xác minh container trong Docker Desktop (hoặc OrbStack) gọi được `host.docker.internal:<PG_PORT>`. Nếu không được thì ghi cách sửa (`listen_addresses`, `pg_hba.conf`) vào `08` mục 2.2 và cập nhật script.
- Gỡ nhãn **[Cần xác minh]** phần macOS trong `08`.

## Acceptance criteria

- [ ] Script chạy xong trên macOS, chạy lần thứ hai không lỗi và không đổi gì.
- [ ] Máy có sẵn cluster cũ ở 5432: cluster cũ giữ nguyên, cluster mới chạy ở cổng khác, `DATABASE_URL` in ra đúng cổng.
- [ ] `psql postgres://fashion:fashion@localhost:<PG_PORT>/fashion` vào được.
- [ ] Từ một container (`docker run --rm postgres psql postgres://fashion:fashion@host.docker.internal:<PG_PORT>/fashion -c 'select 1'`) vào được.
- [ ] `08` không còn nhãn **[Cần xác minh]** về kết nối PostgreSQL trên macOS.
