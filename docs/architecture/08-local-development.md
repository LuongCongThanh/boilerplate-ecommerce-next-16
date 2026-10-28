# 08. Môi trường phát triển local (macOS và Windows WSL2)

> Trạng thái: **Đã duyệt cho MVP**.
> Mọi dịch vụ, kể cả PostgreSQL, chạy bằng **Docker Compose**, nên mọi máy dùng đúng một phiên bản. Trên máy chỉ cần Docker, `uv`, `git`, `make`.

## 1. Tổng quan

```mermaid
graph LR
    subgraph mac [macOS / WSL2]
        subgraph docker [Docker Compose]
            pg[(postgres · :5432)]
            api[api · :8000<br/>runserver + debugpy :5678]
            worker[worker]
            beat[beat]
            relay[relay]
            redis[(redis · :6379)]
            mailpit[mailpit · :1025 / :8025]
        end
    end
    api --> pg
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
| PostgreSQL 18 | Docker, dữ liệu trong named volume `pgdata` | 5432 (mở ra máy để chạy test và dùng IDE) |
| Django API | Docker, code được mount vào container nên sửa code tự reload | 8000 |
| Celery worker, Celery Beat, Outbox relay | Docker, cùng image với API | — |
| Redis (Valkey 8, cùng bản với ElastiCache) | Docker | 6379 |
| Mailpit | Docker | 1025 (SMTP), 8025 (giao diện xem mail) |
| Ảnh Sản phẩm | Ổ đĩa, thư mục `backend/media/` | — |
| VNPay, MoMo | Fake Gateway trong Django | — |
| GHN | Fake, hoặc sandbox thật (gọi ra được từ local) | — |

## 2. Cài đặt lần đầu

### 2.1. Công cụ

#### macOS

```bash
brew install uv
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

3. **uv, git, make, openssl** trong Ubuntu:
   ```bash
   sudo apt install -y git make openssl
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

4. **Clone repo vào trong WSL**, ví dụ `~/projects/`, **không** clone vào `/mnt/c/...`:
   ```bash
   mkdir -p ~/projects && cd ~/projects
   git clone <repo-url>
   git config --global core.autocrlf input
   ```

5. **IDE**: xem mục 6.

| Lỗi hay gặp trên Windows | Cách xử lý |
|---|---|
| Sửa code nhưng server không reload, Docker chậm | Code đang nằm ở `/mnt/c/...`; chuyển repo vào `~/projects/` |
| Lỗi `/bin/sh^M: bad interpreter` | File bị đổi sang CRLF; repo có `.gitattributes` ép LF, chạy `git add --renormalize .` |
| WSL ăn nhiều RAM | Tạo `%UserProfile%\.wslconfig` với `[wsl2]` và `memory=6GB` |

### 2.2. Database

Không cần tạo tay. Service `postgres` trong Compose tạo user `fashion` (mật khẩu `fashion`) và database `fashion` ngay lần chạy đầu. User do image tạo có quyền `CREATEDB`, nên pytest-django tự tạo và xoá database test (`test_fashion`, và `test_fashion_gw0`, `test_fashion_gw1`… khi chạy song song).

Extension `unaccent`, `pg_trgm`, `btree_gist` được tạo bằng migration. Cả ba là trusted extension (từ PostgreSQL 13), nên chủ database tự tạo được, không cần superuser.

Xoá sạch dữ liệu local: `make down` rồi `docker volume rm <project>_pgdata`.

### 2.3. Biến môi trường

```bash
cd backend
cp .env.example .env
```

Các biến chính trong `.env`:

```dotenv
DJANGO_SETTINGS_MODULE=config.settings.local
DATABASE_URL=postgres://fashion:fashion@postgres:5432/fashion
REDIS_URL=redis://redis:6379/0
EMAIL_HOST=mailpit
EMAIL_PORT=1025
JWT_PRIVATE_KEY_PATH=.secrets/jwt_ed25519.pem
JWT_KEY_ID=local-1
REFRESH_REPLAY_KEY_ID=local-replay-1
REFRESH_REPLAY_KEY_PATH=.secrets/refresh_replay.key
STOREFRONT_ORIGIN=http://localhost:3000
PAYMENT_PROVIDER_VNPAY=fake
PAYMENT_PROVIDER_MOMO=fake
SHIPPING_PROVIDER=fake
FAKE_PROVIDERS_ENABLED=true
GOOGLE_OAUTH_CLIENT_ID=
BFF_SHARED_SECRET=local-bff-secret
```

`BFF_SHARED_SECRET` phải trùng với giá trị cấu hình ở Next.js local. Next.js gửi secret này trong header `X-BFF-Secret` kèm `X-Client-IP`, và Django chỉ tin `X-Client-IP` khi secret đúng ([ADR 0009](../adr/0009-nextjs-bff-django-private.md)). Gọi thẳng `localhost:8000` từ Swagger UI hay `curl` vẫn chạy được, chỉ là throttle tính theo IP của máy gọi.

Sinh khoá JWT cho local:

```bash
mkdir -p .secrets && openssl genpkey -algorithm ed25519 -out .secrets/jwt_ed25519.pem
```

Khoá RefreshReplay độc lập JWT, tạo một lần cho local và không commit. Chạy từ backend/ sau khi có .secrets/:

```bash
python -c "from pathlib import Path; import secrets; Path('.secrets/refresh_replay.key').open('xb').write(secrets.token_bytes(32))"
```

Lệnh từ chối ghi đè key đã có; không tạo lại mỗi lần khởi động. Key có ID để xoay và các API replica phải cùng đọc được key còn hiệu lực trong cửa sổ replay. STOREFRONT_ORIGIN chỉ là origin tin cậy, không kèm path/query/userinfo; payment return path do backend cố định.

### 2.4. Chạy

```bash
make up             # docker compose up -d --build
make migrate        # chạy migration rồi sync_beat_schedule (lịch job Celery Beat)
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
| `make makemigrations` / `make migrate` | Tạo / chạy migration; `make migrate` chạy thêm `manage.py sync_beat_schedule` để ghi lịch job vào DB ([07](./07-async-events-jobs.md) mục 3.2) |
| `make load-geo` | Nạp 34 tỉnh/thành và phường/xã |
| `make seed` | Tạo Kho, danh mục, Sản phẩm mẫu, Voucher mẫu |
| `make create-admin` | Tạo Tài khoản Admin (`manage.py create_staff --admin`) |
| `make test` | `pytest -n auto` |
| `make lint` | `ruff check`, `ruff format --check`, `mypy`, `lint-imports` |
| `make fmt` | `ruff format` + `ruff check --fix` |
| `make tunnel` | Mở Cloudflare Tunnel để nghiệm thu với sandbox ([06](./06-integrations.md) mục 8) |

## 4. Debug

- Container `api` chạy `debugpy` ở cổng **5678** (dành cho VS Code).
- Debug Celery task: đặt `CELERY_TASK_ALWAYS_EAGER=True` tạm thời để task chạy ngay trong tiến trình api.
- Cách cấu hình theo từng IDE: xem mục 6.

## 5. Chạy test

- Test dùng database `test_fashion` do pytest-django tự tạo trên PostgreSQL của Compose, mỗi worker `pytest-xdist` một database riêng (không dùng SQLite, để giống production: `select_for_update`, `EXCLUDE`, `unaccent`).
- Celery chạy đồng bộ; API bên ngoài dùng Fake hoặc `respx`; thời gian cố định bằng `time-machine`.
- Có thể chạy test ngay trên máy (hoặc trong WSL), không qua container `api` (PostgreSQL vẫn chạy trong Compose). `.env` trỏ host `postgres` và `redis` (tên service trong Compose), nên phải ghi đè khi chạy từ máy:
  ```bash
  DATABASE_URL=postgres://fashion:fashion@localhost:5432/fashion REDIS_URL=redis://localhost:6379/0 uv run pytest
  ```
  Biến môi trường của shell được ưu tiên hơn giá trị trong `.env`. Run configuration "Pytest (local)" của VS Code và "Pytest" của PyCharm (mục 6) cũng phải đặt hai biến này (thêm khi khởi tạo backend).

## 6. Cấu hình IDE dùng chung

Team dùng cả **VS Code** và **PyCharm**. Repo commit sẵn cấu hình chung để ai clone về cũng chạy và debug được ngay; cấu hình cá nhân không được commit (xem [11-git-workflow.md](./11-git-workflow.md) mục 8).

| IDE | File được commit | Nội dung |
|---|---|---|
| VS Code | `.vscode/launch.json` | "Attach Django (Docker)": attach tới `localhost:5678`, `pathMappings` `${workspaceFolder}/backend` ↔ `/app`; "Pytest (local)": chạy test bằng interpreter `.venv` |
| VS Code | `.vscode/extensions.json` | Extension khuyến nghị: Python, Pylance, Ruff, Mypy Type Checker, Docker, WSL, EditorConfig, Mermaid preview |
| PyCharm | `.run/*.run.xml` | Run configuration lưu dạng file dự án: "Pytest" (đã có), "Django server (Docker Compose)" và "Celery worker (Docker Compose)" (thêm khi khởi tạo backend) |
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
  depends_on:
    postgres: {condition: service_healthy}
    redis: {condition: service_started}

services:
  api:
    <<: *app
    command: python -m debugpy --listen 0.0.0.0:5678 manage.py runserver 0.0.0.0:8000
    ports: ["8000:8000", "5678:5678"]
  worker:
    <<: *app
    command: celery -A config worker -Q default,events,emails,integrations -l info  # local: 1 worker cho cả 4 queue (07 mục 3.1)
  beat:
    <<: *app
    command: celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
  relay:
    <<: *app
    command: python manage.py run_outbox_relay
  postgres:
    image: postgres:18
    environment:
      POSTGRES_USER: fashion        # user do image tạo là superuser trong container, đủ quyền CREATEDB
      POSTGRES_PASSWORD: fashion
      POSTGRES_DB: fashion
    volumes: ["pgdata:/var/lib/postgresql"]
    ports: ["5432:5432"]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U fashion"]
      interval: 2s
  redis:
    image: valkey/valkey:8-alpine   # ghim Valkey 8, cùng bản với ElastiCache
    ports: ["6379:6379"]
  mailpit:
    image: axllent/mailpit
    ports: ["1025:1025", "8025:8025"]

volumes:
  pgdata:
```

Phiên bản image (`postgres`, `valkey`, `mailpit`) sẽ được pin tới bản vá cụ thể khi khởi tạo dự án. Từ image `postgres:18`, volume gắn vào `/var/lib/postgresql` thay cho `/var/lib/postgresql/data` như các bản trước.
