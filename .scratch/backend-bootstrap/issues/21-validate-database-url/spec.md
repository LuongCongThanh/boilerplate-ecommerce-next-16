# `config/env.py` từ chối `DATABASE_URL` sai định dạng ngay khi đọc env

Status: resolved

**PR:** #45

Spec: [spec.md](../../spec.md)

Tách từ ticket [15](../15-docker-compose-local/spec.md) khi sửa review PR #27 ngày 30/10/2026.

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

## Quyết định

Chốt khi grilling ngày 31/10/2026.

| Chủ đề | Quyết định |
|---|---|
| Tài liệu chi phối | `backend/config/env.py` → 08 §2.3 (biến môi trường, dừng ngay khi khởi động), 02 §9.1, §9.4 (comment tiếng Việt). `backend/tests/test_database_url.py` → 02 §9.2, §9.5, 12 §2 |
| Điều kiện từ chối | `database_config()` raise `ImproperlyConfigured` khi `urlsplit` không có username, không có hostname, hoặc tên database (đã `unquote`) rỗng hay chứa `/`, `@`, `:`. Kiểm sau scheme, trước port (review B2): password chứa `/` không mã hoá làm `urlsplit` mất user và hiểu phần sau `:` là port, kiểm port trước thì báo "port không hợp lệ" thay vì chỉ ra URL thiếu user |
| Thông báo lỗi | Nêu phần sai và dạng đúng, ví dụ `DATABASE_URL thiếu user, dạng đúng: postgres://user:pass@host:port/name`. Không chứa giá trị nào của URL |
| `host` truyền vào | URL thiếu host vẫn bị từ chối dù `DATABASE_HOST` khác rỗng: tiến trình chạy trên máy (API, pytest, IDE) dùng chính URL trong `.env`, nên URL phải đủ |
| Seam của AC1 | Unit test `database_config()` cho từng trường hợp, cộng một test chạy `manage.py check` thật (subprocess, `DATABASE_URL` sai qua biến môi trường): exit khác 0, output có `DATABASE_URL`, không có password. Nơi gọi duy nhất là `config/settings/base.py:57`, chạy lúc import settings, nên pytest dừng cùng chỗ |

## Acceptance criteria

- [x] `DATABASE_URL` thiếu user, thiếu host hoặc tên database sai làm `manage.py check` và pytest dừng ngay với `ImproperlyConfigured` nhắc tới `DATABASE_URL`, không tới bước kết nối PostgreSQL.
- [x] Thông báo lỗi không chứa password hay toàn bộ URL.
- [x] Các test hiện có của `test_database_url.py` vẫn pass.
