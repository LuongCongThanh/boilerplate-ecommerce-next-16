# 08. Môi trường phát triển local (macOS và Windows WSL2)

> Trạng thái: **Bản nháp chờ review**.
> **PostgreSQL cài trực tiếp trên máy** (trên Windows: cài trong WSL2). Mọi thứ còn lại chạy bằng **Docker Compose**.

## 1. Tổng quan

```mermaid
graph LR
    subgraph mac [macOS]
        pg[(PostgreSQL 18<br/>Homebrew · :5432)]
        subgraph docker [Docker Compose]
            api[api · :8000<br/>runserver + debugpy :5678]
            worker[worker]
            beat[beat]
            relay[relay]
            redis[(redis · :6379)]
            mailpit[mailpit · :1025 / :8025]
        end
    end
    api -->|host.docker.internal:5432| pg
    worker --> pg
    beat --> pg
    relay --> pg
    api --> redis
    worker --> redis
    beat --> redis
    relay --> redis
    worker --> mailpit
```

| Thành phần | Chạy ở đâu | Cổng |
|---|---|---|
| PostgreSQL 18 | Homebrew trên máy | 5432 |
| Django API | Docker, code được mount vào container nên sửa code tự reload | 8000 |
| Celery worker, Celery Beat, Outbox relay | Docker, cùng image với API | — |
| Redis 7.2 | Docker | 6379 |
| Mailpit | Docker | 1025 (SMTP), 8025 (giao diện xem mail) |
| Ảnh Sản phẩm | Ổ đĩa, thư mục `backend/media/` | — |
| VNPay, MoMo | Fake Gateway trong Django | — |
| GHN | Fake, hoặc sandbox thật (gọi ra được từ local) | — |

## 2. Cài đặt lần đầu

### 2.1. Công cụ

#### macOS

```bash
brew install postgresql@18 uv
brew services start postgresql@18
# Docker Desktop (hoặc OrbStack) cài riêng
```

#### Windows (qua WSL2)

Trên Windows, **mọi thao tác đều làm bên trong WSL2 (Ubuntu)**, không làm trực tiếp trên Windows. Lý do:

- Celery không hỗ trợ chính thức Windows.
- Windows không có sẵn `make`.
- Mount code từ `C:\` vào Docker rất chậm và hay không tự reload khi sửa code.
- Ký tự xuống dòng CRLF làm hỏng script.

Sau khi cài xong, mọi bước từ mục 2.2 trở đi **giống hệt macOS**.

1. **WSL2 + Ubuntu.** Mở PowerShell bằng quyền Administrator:
   ```powershell
   wsl --install -d Ubuntu-24.04
   ```
   Khởi động lại máy, mở "Ubuntu" và tạo user Linux.

2. **Docker Desktop** cài trên Windows. Trong Settings:
   - Bật **General → Use the WSL 2 based engine**.
   - Bật **Resources → WSL integration → Ubuntu-24.04**.

3. **PostgreSQL 18 trong Ubuntu**, cài từ kho apt chính thức của PostgreSQL:
   ```bash
   sudo apt install -y postgresql-common
   sudo /usr/share/postgresql-common/pgdg/apt.postgresql.org.sh
   sudo apt install -y postgresql-18
   sudo service postgresql start
   sudo -u postgres createuser --superuser "$USER"   # để dùng createdb/psql không cần sudo
   ```

4. **uv, git, make, openssl** trong Ubuntu:
   ```bash
   sudo apt install -y git make openssl
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

5. **Clone repo vào trong WSL**, ví dụ `~/projects/`, **không** clone vào `/mnt/c/...`:
   ```bash
   mkdir -p ~/projects && cd ~/projects
   git clone <repo-url>
   git config --global core.autocrlf input
   ```

6. **IDE**: xem mục 6.

| Lỗi hay gặp trên Windows | Cách xử lý |
|---|---|
| Container không kết nối được PostgreSQL | Trong `/etc/postgresql/18/main/postgresql.conf` đặt `listen_addresses = '*'`; trong `pg_hba.conf` thêm `host all all 172.16.0.0/12 scram-sha-256`; chạy `sudo service postgresql restart` |
| PostgreSQL không tự chạy khi mở lại WSL | Thêm `sudo service postgresql start` vào `~/.bashrc`, hoặc bật `systemd=true` trong `/etc/wsl.conf` rồi `sudo systemctl enable postgresql` |
| Sửa code nhưng server không reload, Docker chậm | Code đang nằm ở `/mnt/c/...`; chuyển repo vào `~/projects/` |
| Lỗi `/bin/sh^M: bad interpreter` | File bị đổi sang CRLF; repo có `.gitattributes` ép LF, chạy `git add --renormalize .` |
| WSL ăn nhiều RAM | Tạo `%UserProfile%\.wslconfig` với `[wsl2]` và `memory=6GB` |

### 2.2. Database

```bash
createuser --pwprompt fashion            # nhập mật khẩu, ví dụ: fashion
createdb --owner=fashion fashion
createdb --owner=fashion fashion_test
psql -d fashion -c 'CREATE EXTENSION IF NOT EXISTS unaccent; CREATE EXTENSION IF NOT EXISTS pg_trgm; CREATE EXTENSION IF NOT EXISTS btree_gist;'
psql -d fashion_test -c 'CREATE EXTENSION IF NOT EXISTS unaccent; CREATE EXTENSION IF NOT EXISTS pg_trgm; CREATE EXTENSION IF NOT EXISTS btree_gist;'
```

Extension cũng được tạo bằng migration; lệnh trên giúp user không phải superuser vẫn migrate được.

> **Container kết nối tới PostgreSQL trên máy**: Docker Desktop chuyển `host.docker.internal` về máy thật. Nếu container báo không kết nối được, kiểm tra `listen_addresses` trong `postgresql.conf` và thêm dòng cho dải mạng của Docker vào `pg_hba.conf`, rồi `brew services restart postgresql@18`.

### 2.3. Biến môi trường

```bash
cd backend
cp .env.example .env
```

Các biến chính trong `.env`:

```dotenv
DJANGO_SETTINGS_MODULE=config.settings.local
DATABASE_URL=postgres://fashion:fashion@host.docker.internal:5432/fashion
REDIS_URL=redis://redis:6379/0
EMAIL_HOST=mailpit
EMAIL_PORT=1025
JWT_PRIVATE_KEY_PATH=.secrets/jwt_ed25519.pem
JWT_KEY_ID=local-1
PAYMENT_PROVIDER_VNPAY=fake
PAYMENT_PROVIDER_MOMO=fake
SHIPPING_PROVIDER=fake
GOOGLE_OAUTH_CLIENT_ID=
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001
```

Sinh khoá JWT cho local:

```bash
mkdir -p .secrets && openssl genpkey -algorithm ed25519 -out .secrets/jwt_ed25519.pem
```

### 2.4. Chạy

```bash
make up             # docker compose up -d --build
make migrate        # chạy migration
make load-geo       # nạp 34 tỉnh/thành và phường/xã
make seed           # tạo Kho, danh mục, Sản phẩm mẫu, Voucher mẫu
make create-admin   # tạo tài khoản Admin
```

| Địa chỉ | Dùng để |
|---|---|
| http://localhost:8000/api/docs/ | Swagger UI, gọi thử API |
| http://localhost:8000/admin/ | Django Admin read-only, xem dữ liệu |
| http://localhost:8025 | Mailpit, xem email đã gửi |
| http://localhost:8000/dev/fake-gateway/ | Fake Gateway |

## 3. Lệnh hằng ngày (`Makefile`)

| Lệnh | Làm gì |
|---|---|
| `make up` / `make down` | Bật / tắt các container |
| `make logs s=worker` | Xem log của một service |
| `make shell` | `manage.py shell` trong container api |
| `make makemigrations` / `make migrate` | Tạo / chạy migration |
| `make test` | `pytest -n auto` |
| `make lint` | `ruff check`, `ruff format --check`, `mypy`, `lint-imports` |
| `make fmt` | `ruff format` + `ruff check --fix` |
| `make tunnel` | Mở Cloudflare Tunnel để nghiệm thu với sandbox ([06](./06-integrations.md) mục 8) |

## 4. Debug

- Container `api` chạy `debugpy` ở cổng **5678** (dành cho VS Code).
- Debug Celery task: đặt `CELERY_TASK_ALWAYS_EAGER=True` tạm thời để task chạy ngay trong tiến trình api.
- Cách cấu hình theo từng IDE: xem mục 6.

## 5. Chạy test

- Test dùng database `fashion_test` trên PostgreSQL của máy (không dùng SQLite, để giống production: `select_for_update`, `EXCLUDE`, `unaccent`).
- Celery chạy đồng bộ; API bên ngoài dùng Fake hoặc `respx`; thời gian cố định bằng `time-machine`.
- Có thể chạy test ngay trên máy (hoặc trong WSL), không qua Docker: `uv run pytest` với `DATABASE_URL` trỏ `localhost`.

## 6. Cấu hình IDE dùng chung

Team dùng cả **VS Code** và **PyCharm**. Repo commit sẵn cấu hình chung để ai clone về cũng chạy và debug được ngay; cấu hình cá nhân không được commit (xem [11-git-workflow.md](./11-git-workflow.md) mục 8).

| IDE | File được commit | Nội dung |
|---|---|---|
| VS Code | `.vscode/launch.json` | "Attach Django (Docker)": attach tới `localhost:5678`, `pathMappings` `${workspaceFolder}/backend` ↔ `/app`; "Pytest (local)": chạy test bằng interpreter `.venv` |
| VS Code | `.vscode/extensions.json` | Extension khuyến nghị: Python, Pylance, Ruff, Mypy Type Checker, Docker, WSL, EditorConfig, Mermaid preview |
| PyCharm | `.run/*.run.xml` | Run configuration lưu dạng file dự án: "Django server (Docker Compose)", "Celery worker (Docker Compose)", "Pytest" |
| Cả hai | `.editorconfig` | Thụt lề 4 dấu cách cho Python, 2 cho YAML/JSON/TOML; LF; UTF-8; xoá khoảng trắng cuối dòng |

### 6.1. VS Code

- **Windows**: mở VS Code, bấm "Connect to WSL", rồi mở thư mục `~/projects/<repo>`. Mọi extension Python chạy bên trong WSL.
- Chọn interpreter `backend/.venv` (tạo bằng `uv sync` để IDE hiểu code và chạy test; Django vẫn chạy trong Docker).
- Debug: `make up`, sau đó chọn "Attach Django (Docker)" và nhấn F5. Breakpoint đặt trong `backend/` sẽ dừng đúng chỗ.

### 6.2. PyCharm

- Interpreter: **Docker Compose**, service `api`. Cách này cho phép chạy và debug Django, Celery ngay trong container bằng debugger của PyCharm, nên **không** dùng cổng `debugpy` 5678.
- **Windows**: dùng interpreter WSL, hoặc Docker Compose qua Docker Desktop. Mở project từ đường dẫn `\\wsl$\Ubuntu-24.04\home\<user>\projects\<repo>`.
- Tính năng Docker Compose interpreter và interpreter WSL cần **PyCharm Professional** (hoặc gói giấy phép có các tính năng này) **[Cần xác minh theo giấy phép team đang dùng]**. Nếu không có, PyCharm vẫn dùng được với interpreter `backend/.venv` để chạy test và gợi ý code; còn debug Django trong Docker thì dùng VS Code.
- Đánh dấu `backend/` là Sources Root để import `config`, `shared`, `modules` không bị báo lỗi.

## 7. `docker-compose.yml` (rút gọn)

```yaml
x-app: &app
  build: .
  env_file: .env
  volumes: [".:/app"]
  extra_hosts: ["host.docker.internal:host-gateway"]
  depends_on: [redis]

services:
  api:
    <<: *app
    command: python -m debugpy --listen 0.0.0.0:5678 manage.py runserver 0.0.0.0:8000
    ports: ["8000:8000", "5678:5678"]
  worker:
    <<: *app
    command: celery -A config worker -Q default,events,emails,integrations -l info
  beat:
    <<: *app
    command: celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
  relay:
    <<: *app
    command: python manage.py run_outbox_relay
  redis:
    image: redis:7.2-alpine
    ports: ["6379:6379"]
  mailpit:
    image: axllent/mailpit
    ports: ["1025:1025", "8025:8025"]
```

Phiên bản image (`mailpit`) sẽ được pin cụ thể khi khởi tạo dự án.
