# Thống nhất tài liệu môi trường local và hook pre-commit

Status: resolved

## Bối cảnh

- Phần PostgreSQL đã chốt ở [ADR 0015](../../../docs/adr/0015-local-postgres-on-host.md): PostgreSQL cài trên máy (macOS bằng Homebrew, Windows trong WSL2 Ubuntu bằng apt), bản major mới nhất, cài bằng `scripts/setup/postgres.sh`. `02`, `08` và README đã được sửa theo ADR này. Việc chạy thử bộ cài nằm ở ticket 08.
- Môi trường dev trên Windows giữ nguyên như `08`: code, uv, make và pytest chạy trong WSL2 Ubuntu-24.04, repo nằm ở `~/projects`. Các service còn lại (api, worker, beat, relay, redis, mailpit) vẫn chạy trong Docker Compose.
- Ticket này xử lý các chỗ lệch còn lại trong `02` và `.pre-commit-config.yaml`, cần xong trước khi dựng khung backend (ticket 07).

## Việc cần làm

### `docs/architecture/02-backend-structure.md`

- Mục 5: xoá khối `scripts/` bị lặp lần thứ hai.
- Mục 2: cột phiên bản của `uv` đổi thành `≥ 0.13`.

### `docs/architecture/08-local-development.md`

- Mục 2.1: ghi yêu cầu `uv ≥ 0.13`.

### `.pre-commit-config.yaml`

- Theo `02` mục 5: thêm hook `mypy` và `lint-imports` (hook `local`, chạy bằng `uv run` trong `backend/`).
- Giới hạn `ruff-check`, `ruff-format`, `mypy`, `lint-imports` bằng `files: ^backend/`. Các hook chung (gitleaks, pre-commit-hooks, commitizen) giữ nguyên.
- Hook `mypy` và `lint-imports` phải bỏ qua êm khi chưa có `backend/pyproject.toml`, để không chặn commit cho tới khi ticket 07 xong.

## Acceptance criteria

- [x] Cây thư mục ở `02` mục 5 không còn khối lặp.
- [x] `02` và `08` cùng ghi `uv ≥ 0.13`.
- [x] `pre-commit run --all-files` qua khi chưa có `backend/`; hook ruff, mypy, import-linter chỉ chạy trên file trong `backend/`.

**PR:** (điền số PR khi mở)

## Comments

- 29/10/2026: Khối `scripts/` lặp trong `02` mục 5 đã được gỡ từ trước. `02` ghi `uv ≥ 0.13`; `08` ghi `uv ≥ 0.13` ở phần yêu cầu đầu file. Hook `mypy` và `lint-imports` là hook `local`, chạy `uv run` trong `backend/` và thoát 0 khi chưa có `backend/pyproject.toml`. `pre-commit run --all-files` qua; `end-of-file-fixer` đã thêm dòng trống cuối cho `.run/Pytest.run.xml`.
