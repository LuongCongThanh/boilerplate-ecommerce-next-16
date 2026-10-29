# `config/env.py` từ chối `DATABASE_URL` sai định dạng ngay khi đọc env

Status: ready-for-agent

Spec: [spec.md](../spec.md)

Tách từ ticket [15](./15-docker-compose-local.md) khi sửa review PR #27 ngày 30/10/2026.

## Bối cảnh

`database_config()` trong `config/env.py` chỉ kiểm tra scheme (`postgres`/`postgresql`) và port. URL thiếu user, host hoặc sai cấu trúc vẫn được nhận: phần còn lại rơi hết vào `NAME`, còn `USER`, `HOST` để rỗng. Lỗi chỉ lộ ra khi mở kết nối, với thông báo không chỉ về `.env`.

Đã gặp thật khi chạy pytest trên máy dev: một password bị chèn sai chỗ trong `DATABASE_URL`, pytest-django báo `fe_sendauth: no password supplied` và in nguyên chuỗi (kèm password) trong `dbname=…`. Tái hiện (password thay bằng `secret`):

```
>>> database_config("postgres:///secret//fashion:fashion@localhost:5432/fashion")
{'NAME': 'secret//fashion:fashion@localhost:5432/fashion', 'USER': '', 'HOST': '', 'PORT': '5432', ...}
```

## Việc cần làm

- `database_config()` raise `ImproperlyConfigured` khi URL thiếu user, thiếu host, hoặc tên database rỗng hay chứa `/`, `@`, `:`.
- Thông báo lỗi chỉ ra biến `DATABASE_URL` và dạng đúng (`postgres://user:pass@host:port/name`), **không** chứa giá trị URL hay password (như thông báo của `PII_HMAC_KEYS`).
- Giữ hành vi đang có: URL không có password vẫn hợp lệ (`test_allows_url_without_password`), tham số query giữ trong `OPTIONS`, `host` truyền vào vẫn thay host của URL.
- Thêm test vào `backend/tests/test_database_url.py` cho từng trường hợp bị từ chối.

## Acceptance criteria

- [ ] `DATABASE_URL` thiếu user, thiếu host hoặc tên database sai làm `manage.py check` và pytest dừng ngay với `ImproperlyConfigured` nhắc tới `DATABASE_URL`, không tới bước kết nối PostgreSQL.
- [ ] Thông báo lỗi không chứa password hay toàn bộ URL.
- [ ] Các test hiện có của `test_database_url.py` vẫn pass.
