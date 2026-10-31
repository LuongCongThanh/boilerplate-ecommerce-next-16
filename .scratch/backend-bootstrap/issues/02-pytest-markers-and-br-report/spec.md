# Khai báo marker pytest và lệnh `make br-report`

Status: ready-for-agent

Blocked by: 07

Spec: [spec.md](../../spec.md)

## Việc cần làm

- Làm cùng lúc khởi tạo backend (khi có `backend/pyproject.toml`).
- Trong `pyproject.toml`, bật `--strict-markers` và khai báo 3 marker `br`, `concurrency`, `flow` theo `docs/architecture/12-testing-strategy.md` mục 3.
- Viết lệnh `make br-report`: lấy mọi mã `BR-xxx` trong `docs/business/04-business-rules.md`, so với các mã gắn trong `@pytest.mark.br(...)` (thu thập bằng `pytest --collect-only`), rồi in ra các mã chưa có test.
- `make br-report` không chạy trong CI.

## Acceptance criteria

- [ ] Test dùng marker chưa khai báo thì pytest báo lỗi.
- [ ] `pytest -m concurrency` và `pytest -m flow` chỉ chạy đúng nhóm test đó.
- [ ] `make br-report` in đúng danh sách mã `BR-xxx` chưa có test và luôn thoát với mã 0.
