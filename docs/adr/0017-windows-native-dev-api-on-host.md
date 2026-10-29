# Windows dev không qua WSL2, API chạy trên máy

Thay phần Windows và phần "API chạy trong Compose" của [ADR 0015](./0015-local-postgres-on-host.md). Phần còn lại của 0015 (PostgreSQL cài trên máy, bản major mới nhất, extension do migration tạo) vẫn giữ.

Trên Windows, dự án dev thẳng trên Windows, không qua WSL2. PostgreSQL cài bằng bộ cài EDB (hoặc `winget install PostgreSQL.PostgreSQL.<major>`), sau đó `scripts/setup/postgres.ps1` tạo role và database `fashion`; `scripts/setup/postgres.sh` chỉ còn dùng cho macOS và Ubuntu. Trên **mọi hệ điều hành**, Django API chạy trên máy bằng `uv run`; Docker Compose chỉ còn worker, beat, relay, redis, mailpit và service `migrate`.

Bốn lý do trước đây bắt Windows phải dùng WSL2 được xử lý như sau:

- **Celery không hỗ trợ Windows**: worker và beat chạy trong container Linux, không chạy trên Windows.
- **Windows không có `make`**: cài GNU make (`winget install ezwinports.make` hoặc `choco install make`) và giữ `Makefile`. Recipe chỉ gọi `uv run` hoặc `docker compose`, không dùng cú pháp riêng của shell POSIX.
- **Mount code từ ổ Windows vào Docker chậm, không tự reload**: API, thứ cần reload liên tục, chạy trên máy nên không mount. Worker, beat, relay vẫn bind mount `backend/`; Celery không tự reload, sửa code xong thì chạy `make restart-worker`, mount chậm chỉ ảnh hưởng lúc khởi động.
- **CRLF làm hỏng script**: `.gitattributes` ép LF cho mọi file văn bản, riêng `*.ps1`, `*.bat`, `*.cmd` giữ CRLF.

## Hệ quả

- `.env` viết cho máy: `DATABASE_URL`, `REDIS_URL`, `EMAIL_HOST` trỏ `localhost`. Container ghi đè các biến cần khác trong khối `environment:` của `docker-compose.yml` (`host.docker.internal` cho PostgreSQL, tên service cho Redis và Mailpit).
- Redis của Compose mở ra máy ở cổng `REDIS_PORT` (mặc định 6380), để không tranh cổng 6379 với Redis hay Memurai mà máy có thể đã cài cho project khác.
- Bộ cài trên Windows không tự cài PostgreSQL: việc cài cần quyền Admin và mật khẩu superuser `postgres`, làm tay một lần. `postgres.ps1` hỏi mật khẩu đó (nhập ẩn) mỗi lần chạy và không lưu lại.
- Trên Windows, cổng của PostgreSQL do bộ cài EDB chọn; `postgres.ps1` đọc cổng từ cluster đang chạy chứ không tự chọn cổng trống như `postgres.sh`.
- Debug Django dùng debugger của IDE chạy thẳng trên máy, không còn cổng `debugpy` 5678 trong container. Interpreter của IDE là `backend/.venv`, không cần PyCharm Professional.
- Local Windows chạy PostgreSQL bản Windows, còn CI và production chạy Linux. Khác biệt về collation và locale có thể chỉ lộ ra trên CI.
