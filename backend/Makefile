# Lệnh hằng ngày (08 mục 3). Mỗi lệnh thêm cùng ticket tạo ra thứ nó gọi;
# lệnh dùng container (up, down, migrate…) thêm ở ticket 15.
.PHONY: test lint fmt

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
