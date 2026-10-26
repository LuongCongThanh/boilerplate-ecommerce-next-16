# Chặn coverage dưới 80% cho `modules/*/services` trong CI

Status: needs-triage

## Việc cần làm

- Làm cùng lúc khởi tạo backend (khi có `backend/pyproject.toml`); trước đó job `backend` trong CI bỏ qua mọi bước.
- Chạy test kèm đo coverage, rồi thêm bước riêng trong job `backend` của `.github/workflows/ci.yml`:
  `coverage report --include="modules/*/services/*" --fail-under=80`.
- Không đặt `fail_under` trong `pyproject.toml`, vì giá trị đó áp cho toàn repo. Xem `docs/architecture/02-backend-structure.md` §9.5.

## Acceptance criteria

- [ ] PR có coverage `modules/*/services` dưới 80% bị CI chặn.
- [ ] Không có ngưỡng coverage cho toàn repo.
