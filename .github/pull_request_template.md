<!--
Tiêu đề PR theo Conventional Commits, ví dụ: feat(ordering): add COD checkout
PR thường merge vào `dev` bằng squash. PR release `dev` → `main` dùng merge commit.
Xem docs/architecture/11-git-workflow.md
-->

## Làm gì

<!-- Mô tả ngắn thay đổi -->

## Vì sao

<!-- Bối cảnh, vấn đề cần giải quyết -->

## Liên kết

- Ticket:
- User story: US-
- Quy tắc nghiệp vụ: BR-

## Checklist

- [ ] Đã có test cho thay đổi (service, handler hoặc API)
- [ ] Đã tạo migration nếu đổi model, và migration tương thích ngược
- [ ] Đã chạy `make lint` và `make test`
- [ ] Không vi phạm ranh giới module (`lint-imports` xanh)
- [ ] Đã cập nhật tài liệu, `GLOSSARY.md` hoặc ADR nếu cần
- [ ] Không có secret, token, dữ liệu cá nhân thật trong code, log hoặc test

## Ghi chú cho người review

<!-- Chỗ cần xem kỹ, cách test thủ công, ảnh chụp Swagger… -->
