# Lệnh hằng ngày (08 mục 3). Mỗi lệnh thêm cùng ticket tạo ra thứ nó gọi.
# Recipe chỉ gọi `uv run`, `docker compose` hoặc target khác qua `$(MAKE)`, không dùng cú pháp
# riêng của shell POSIX, để chạy được bằng GNU make trên Windows (ADR 0017).
.PHONY: test lint fmt up down run restart-worker logs shell makemigrations migrate load-geo db-reset

test:
	uv run pytest -n auto

lint:
	uv run ruff check .
	uv run ruff format --check .
	uv run mypy .
	uv run lint-imports

fmt:
	uv run ruff format .
	uv run ruff check --fix .

# Service migrate chạy migrate và sync_beat_schedule trước khi worker, beat khởi động (08 mục 7)
up:
	docker compose up -d --build

down:
	docker compose down

# API chạy trên máy, tự reload khi sửa code
run:
	uv run python manage.py runserver

# Celery không tự reload: chạy sau khi sửa code
restart-worker:
	docker compose restart worker beat

# make logs s=worker
logs:
	docker compose logs -f $(s)

shell:
	uv run python manage.py shell

makemigrations:
	uv run python manage.py makemigrations

# Chạy trên máy; sync_beat_schedule ghi lịch job vào DB (07 mục 3.2)
migrate:
	uv run python manage.py migrate
	uv run python manage.py sync_beat_schedule

# Nạp tỉnh/thành, phường/xã sau migrate (08 mục 2.4 bước 4); chạy lại không trùng, không xoá mã cũ
load-geo:
	uv run python manage.py load_geo

# Xoá và tạo lại database fashion rồi chạy target migrate (08 mục 2.2); reset_db chỉ chạy với
# DEBUG bật và host localhost
db-reset:
	uv run python manage.py reset_db
	$(MAKE) migrate
