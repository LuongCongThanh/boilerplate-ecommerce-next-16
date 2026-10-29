# Test tải bằng k6 trên staging

Status: needs-triage

## Việc cần làm

- Việc sau MVP, làm trước đợt khuyến mãi lớn đầu tiên. Xem `docs/architecture/12-testing-strategy.md` mục 9.
- Viết kịch bản k6 theo mục tiêu ở `docs/architecture/10-nfr.md` mục 1: p95 API đọc ≤ 300 ms, p95 `POST /store/checkout` ≤ 800 ms, 50 request/giây và 10 đơn/giây.
- Kịch bản checkout dồn vào một Biến thể có Tồn kho ít, để kiểm tra không bán vượt Tồn kho dưới tải.
- Chạy trên staging, dùng Fake Gateway; không chạy trên production.

## Acceptance criteria

- [ ] Có kịch bản k6 commit trong repo và hướng dẫn chạy.
- [ ] Có biên bản kết quả một lần chạy trên staging, so với các mục tiêu ở `10-nfr.md`.
- [ ] Sau lần chạy, Tồn kho không âm và số đơn thành công không vượt Tồn kho ban đầu.
