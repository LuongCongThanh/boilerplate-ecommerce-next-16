# Chặn branch coverage dưới 80% cho `services` và `handlers` của từng module trong CI

Status: needs-triage

## Việc cần làm

- Làm cùng lúc khởi tạo backend (khi có `backend/pyproject.toml`); trước đó job `backend` trong CI bỏ qua mọi bước.
- Thêm `pytest-cov` vào dependency dev. Trong `pyproject.toml`, đặt `[tool.coverage.run] branch = true`.
- Chạy test bằng `pytest -n auto --cov=modules --cov-report=`. `pytest-cov` gom dữ liệu coverage từ các worker của `pytest-xdist`; `coverage run` không làm được việc này.
- Thêm bước riêng trong job `backend` của `.github/workflows/ci.yml`, kiểm tra **từng module**, để module phủ tốt không che module phủ kém:

  ```bash
  fail=0
  for m in modules/*/; do
    m=${m%/}
    [ -d "$m/services" ] || [ -f "$m/handlers.py" ] || continue
    coverage report --include="$m/services/*,$m/handlers.py" --fail-under=80 || fail=1
  done
  exit $fail
  ```

- Không đặt `fail_under` trong `pyproject.toml`, vì giá trị đó áp cho toàn repo. Xem `docs/architecture/12-testing-strategy.md` mục 8.

## Acceptance criteria

- [ ] PR có branch coverage của `services/` hoặc `handlers.py` dưới 80% ở bất kỳ module nào thì bị CI chặn.
- [ ] Module A đạt 100% không giúp module B đạt 60% qua cổng.
- [ ] Module chưa có `services/` và `handlers.py` không làm bước này lỗi.
- [ ] Coverage đo đúng khi chạy song song bằng `pytest -n auto` (kết quả bằng khi chạy tuần tự).
- [ ] Không có ngưỡng coverage cho toàn repo.
