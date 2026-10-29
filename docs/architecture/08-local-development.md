# 08. Môi trường phát triển local (macOS và Windows WSL2)

> Trạng thái: **Đã chốt cho MVP** ([quy ước](../../README.md#trạng-thái-tài-liệu)).
> **PostgreSQL cài trên máy** (macOS: Homebrew; Windows: trong WSL2 Ubuntu), bằng bộ cài `scripts/setup/postgres.sh` ([ADR 0015](../adr/0015-local-postgres-on-host.md)). Các dịch vụ còn lại chạy bằng **Docker Compose**. Trên máy cần Docker, `uv` ≥ 0.13 (uv tự tải Python 3.14 theo `backend/.python-version`), `git`, `make`.

## 1. Tổng quan

```mermaid
graph LR
    subgraph mac [macOS / WSL2]
        pg[(PostgreSQL bản mới nhất · :5432<br/>cài trên máy)]
        subgraph docker [Docker Compose]
            api[api · :8000<br/>runserver + debugpy :5678]
            worker[worker]
            beat[beat]
            relay[relay]
            redis[(redis · :6379)]
            mailpit[mailpit · :1025 / :8025]
        end
    end
    api -- host.docker.internal --> pg
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
| PostgreSQL (bản major mới nhất) | Cài trên máy: Homebrew (macOS), apt PGDG trong WSL2 Ubuntu (Windows). Container gọi qua `host.docker.internal` | 5432, hoặc cổng trống kế tiếp nếu 5432 đang bận (`PG_PORT`) |
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

PostgreSQL: xem mục 2.2.

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

   Bật networking mirrored để container Docker và Windows gọi được PostgreSQL chạy trong WSL. Tạo hoặc sửa `%UserProfile%\.wslconfig`:
   ```ini
   [wsl2]
   networkingMode=mirrored
   ```
   Rồi chạy `wsl --shutdown` trong PowerShell để áp dụng. Cần Windows 11 22H2 trở lên.

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

PostgreSQL cài trên máy, không chạy trong Docker ([ADR 0015](../adr/0015-local-postgres-on-host.md)). Từ gốc repo, chạy (trên Windows thì chạy trong Ubuntu của WSL):

```bash
bash scripts/setup/postgres.sh
```

Script làm các việc sau, chạy lại nhiều lần vẫn an toàn:

1. Kiểm tra `git`, `make`, `docker`, `uv` (chỉ báo thiếu, không tự cài).
2. Tìm bản major mới nhất: macOS lấy `postgresql@<major>` trên Homebrew, Ubuntu/WSL thêm repo PGDG rồi lấy `postgresql-<major>`. Máy đã có bản đó thì dùng luôn, chưa có thì cài.
3. Không đụng tới cluster PostgreSQL khác đang có. Nếu cổng 5432 đã bị cluster khác giữ, cluster mới chạy ở cổng trống kế tiếp (5433…).
4. Tạo role `fashion` (mật khẩu `fashion`, quyền `CREATEDB`) và database `fashion`. Nhờ `CREATEDB`, pytest-django tự tạo và xoá database test (`test_fashion`, và `test_fashion_gw0`, `test_fashion_gw1`… khi chạy song song).
5. Kiểm tra extension `unaccent`, `pg_trgm`, `btree_gist` có sẵn để cài. Extension do **migration** tạo, giống CI và RDS. Cả ba là trusted extension (từ PostgreSQL 13), nên chủ database tự tạo được, không cần superuser.
6. Thử đăng nhập bằng `fashion` qua `localhost`, rồi in `DATABASE_URL` và `PG_PORT` để chép vào `backend/.env` (mục 2.3). Trên WSL, script nhắc nếu chưa bật networking mirrored.

Production (RDS) và CI (`postgres:18`) có thể chạy bản major cũ hơn local: không dùng tính năng chỉ có ở bản mới; CI sẽ bắt lỗi này.

Kết nối:

- IDE, `psql`, pytest chạy trên máy hoặc trong WSL: `localhost:<PG_PORT>`.
- Container trong Compose: `host.docker.internal:<PG_PORT>` (mục 7). Trên Windows cần `networkingMode=mirrored` (mục 2.1) **[Cần xác minh]**; trên macOS **[Cần xác minh]**. Nếu container không kết nối được thì cách sửa sẽ được ghi ở đây (ticket `.scratch/backend-bootstrap/issues/08-local-postgres-installer.md`).

Dữ liệu nằm trên máy (hoặc trong WSL), nên `make down` không làm mất dữ liệu. Thường không cần xoá; chỉ xoá khi migration bị rối (đổi qua lại giữa các nhánh có migration xung đột) hoặc muốn seed lại từ đầu: `make db-reset` (drop và tạo lại database `fashion`, giữ role, rồi migrate). `wsl --unregister` sẽ xoá luôn dữ liệu; khi đó chạy lại script và seed lại (mục 2.4).

### 2.3. Biến môi trường

```bash
cd backend
cp .env.example .env
```

Các biến chính trong `.env`. Mỗi biến được khai báo trong `config/env.py` ở mốc đầu tiên dùng tới nó ([roadmap](../../.scratch/mvp-roadmap/map.md)); `.env.example` chỉ chứa biến đã khai báo. Thiếu biến bắt buộc thì Django dừng ngay khi khởi động và báo tên biến.

```dotenv
# Từ M0
DJANGO_SETTINGS_MODULE=config.settings.local
DJANGO_SECRET_KEY=local-only-change-me
DATABASE_URL=postgres://fashion:fashion@localhost:5432/fashion   # theo output của scripts/setup/postgres.sh
PG_PORT=5432                                                      # Compose dùng để trỏ host.docker.internal
REDIS_URL=redis://redis:6379/0
EMAIL_HOST=mailpit
EMAIL_PORT=1025
PII_HMAC_KEYS=local-pii-1:local-pii-secret                # kid:secret, khoá đầu dùng cho giá trị mới, không xoá khoá cũ (ADR 0016)
STOREFRONT_ORIGIN=http://localhost:3000
BFF_SHARED_SECRET=local-bff-secret

# Từ M1 (đăng nhập, JWT, refresh)
JWT_PRIVATE_KEY_PATH=.secrets/jwt_ed25519.pem
JWT_KEY_ID=local-1
REFRESH_REPLAY_KEY_ID=local-replay-1
REFRESH_REPLAY_KEY_PATH=.secrets/refresh_replay.key

# Từ M2 (checkout COD, Fake GHN)
QUOTE_SIGNING_KEYS=local-quote-1:local-quote-secret       # kid:secret, nhiều khoá cách nhau bằng dấu phẩy, khoá đầu dùng để ký (04 mục 5.3)
SHIPPING_PROVIDER=fake
FAKE_PROVIDERS_ENABLED=true

# Từ M3 (thanh toán online)
PAYMENT_PROVIDER_VNPAY=fake
PAYMENT_PROVIDER_MOMO=fake

# Từ M6 (đăng nhập Google)
GOOGLE_OAUTH_CLIENT_ID=
```

`BFF_SHARED_SECRET` phải trùng với giá trị cấu hình ở Next.js local. Next.js gửi secret này trong header `X-BFF-Secret` kèm `X-Client-IP`, và Django chỉ tin `X-Client-IP` khi secret đúng ([ADR 0009](../adr/0009-nextjs-bff-django-private.md)). Gọi thẳng `localhost:8000` từ Swagger UI hay `curl` vẫn chạy được, chỉ là throttle tính theo IP của máy gọi.

Từ M1, sinh khoá JWT cho local:

```bash
mkdir -p .secrets && openssl genpkey -algorithm ed25519 -out .secrets/jwt_ed25519.pem
```

Khoá RefreshReplay độc lập JWT, tạo một lần cho local và không commit. Chạy từ backend/ sau khi có .secrets/:

```bash
uv run python -c "from pathlib import Path; import secrets; Path('.secrets/refresh_replay.key').open('xb').write(secrets.token_bytes(32))"
```

Lệnh từ chối ghi đè key đã có; không tạo lại mỗi lần khởi động. Key có ID để xoay và các API replica phải cùng đọc được key còn hiệu lực trong cửa sổ replay. STOREFRONT_ORIGIN chỉ là origin tin cậy, không kèm path/query/userinfo; payment return path do backend cố định.

### 2.4. Chạy

```bash
make up             # docker compose up -d --build; service migrate chạy migration và sync_beat_schedule trước khi api, worker, beat, relay khởi động (mục 7)
make load-geo       # nạp 34 tỉnh/thành và phường/xã
make create-admin   # tạo tài khoản Admin
make seed           # (từ M1) tạo Kho, danh mục, Sản phẩm mẫu; Voucher mẫu từ M2
```

`make migrate` chỉ cần khi đã có migration mới mà không muốn khởi động lại container.

| Địa chỉ | Dùng để |
|---|---|
| http://localhost:8000/api/docs/ | Swagger UI, gọi thử API |
| http://localhost:8025 | Mailpit, xem email đã gửi |
| http://localhost:8000/dev/fake-gateway/ | Fake Gateway (từ M3) |

Không có Django Admin ([ADR 0004](../adr/0004-custom-nextjs-admin.md)). Xem dữ liệu bằng `psql`, công cụ database của IDE hoặc `make shell`.

## 3. Lệnh hằng ngày (`Makefile`)

Mỗi lệnh được thêm vào `Makefile` cùng ticket tạo ra lệnh mà nó gọi, nên cột "Có từ" cho biết lệnh nào đã dùng được.

| Lệnh | Làm gì | Có từ |
|---|---|---|
| `make up` / `make down` | Bật / tắt các container; `make up` chạy service `migrate` trước (mục 7) | M0 (ticket 07) |
| `make logs s=worker` | Xem log của một service | M0 (ticket 07) |
| `make shell` | `manage.py shell` trong container api | M0 (ticket 07) |
| `make makemigrations` / `make migrate` | Tạo / chạy migration; `make migrate` chạy thêm `manage.py sync_beat_schedule` để ghi lịch job vào DB ([07](./07-async-events-jobs.md) mục 3.2) | M0 (ticket 07) |
| `make db-reset` | Xoá và tạo lại database `fashion` rồi migrate (mục 2.2) | M0 (ticket 07) |
| `make test` | `pytest -n auto` | M0 (ticket 07) |
| `make lint` | `ruff check`, `ruff format --check`, `mypy`, `lint-imports`, `scripts/gen_importlinter.py --check` | M0 (ticket 07) |
| `make fmt` | `ruff format` + `ruff check --fix` | M0 (ticket 07) |
| `make load-geo` | Nạp 34 tỉnh/thành và phường/xã | M0 (ticket 09) |
| `make create-admin` | Tạo Tài khoản Admin (`manage.py create_staff --admin`) | M0 (ticket 12) |
| `make seed` | Tạo Kho, danh mục, Sản phẩm mẫu, Voucher mẫu | M1 (Voucher mẫu từ M2) |
| `make tunnel` | Mở Cloudflare Tunnel để nghiệm thu với sandbox ([06](./06-integrations.md) mục 8) | M7 |

## 4. Debug

- Container `api` chạy `debugpy` ở cổng **5678** (dành cho VS Code).
- Debug Celery task: đặt `CELERY_TASK_ALWAYS_EAGER=True` tạm thời để task chạy ngay trong tiến trình api.
- Cách cấu hình theo từng IDE: xem mục 6.

## 5. Chạy test

- Test dùng database `test_fashion` do pytest-django tự tạo trên PostgreSQL cài trên máy, mỗi worker `pytest-xdist` một database riêng (không dùng SQLite, để giống production: `select_for_update`, `EXCLUDE`, `unaccent`).
- Celery chạy đồng bộ; API bên ngoài dùng Fake hoặc `respx`; thời gian cố định bằng `time-machine`.
- Có thể chạy test ngay trên máy (hoặc trong WSL), không qua container `api`. `DATABASE_URL` trong `.env` đã trỏ `localhost:<PG_PORT>`, nhưng `REDIS_URL` trỏ host `redis` (tên service trong Compose), nên phải ghi đè khi chạy từ máy:
  ```bash
  REDIS_URL=redis://localhost:6379/0 uv run pytest
  ```
  Biến môi trường của shell được ưu tiên hơn giá trị trong `.env`. Run configuration "Pytest (local)" của VS Code và "Pytest" của PyCharm (mục 6) cũng phải đặt biến này (thêm khi khởi tạo backend).

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
  environment:
    # PostgreSQL cài trên máy (mục 2.2); trong container, localhost là chính container
    DATABASE_URL: postgres://fashion:fashion@host.docker.internal:${PG_PORT:-5432}/fashion
  extra_hosts: ["host.docker.internal:host-gateway"]   # Docker Desktop đã có sẵn; Docker Engine trên Linux không được hỗ trợ (PostgreSQL chỉ nghe localhost)
  volumes: [".:/app"]
  depends_on:
    redis: {condition: service_started}
    migrate: {condition: service_completed_successfully}  # beat cần bảng django_celery_beat, relay cần bảng outbox

services:
  migrate:
    build: .
    env_file: .env
    environment:
      DATABASE_URL: postgres://fashion:fashion@host.docker.internal:${PG_PORT:-5432}/fashion
    extra_hosts: ["host.docker.internal:host-gateway"]
    volumes: [".:/app"]
    command: sh -c "python manage.py migrate && python manage.py sync_beat_schedule"
    restart: "no"
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
  redis:
    image: valkey/valkey:8-alpine   # ghim Valkey 8, cùng bản với ElastiCache
    ports: ["6379:6379"]
  mailpit:
    image: axllent/mailpit
    ports: ["1025:1025", "8025:8025"]
```

Phiên bản image (`valkey`, `mailpit`) sẽ được pin tới bản vá cụ thể khi khởi tạo dự án. Compose không có service `postgres` ([ADR 0015](../adr/0015-local-postgres-on-host.md)); `PG_PORT` đọc từ `.env` để Compose thay vào `DATABASE_URL`. Service `migrate` chạy một lần rồi thoát; `api`, `worker`, `beat`, `relay` chỉ khởi động khi nó thoát thành công, nên DB trống không làm `beat` hay `relay` lỗi liên tục. Migration lỗi thì `make up` dừng ở bước này, xem bằng `make logs s=migrate`.
