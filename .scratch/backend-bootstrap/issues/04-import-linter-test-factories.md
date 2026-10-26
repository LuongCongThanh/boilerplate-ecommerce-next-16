# Ranh giới `import-linter` cho test và factory

Status: needs-triage

## Việc cần làm

- Không thêm contract riêng cho factory. Contract `layers` đã chặn test của module lớp dưới import factory của module lớp trên, và chặn hai module cùng lớp import lẫn nhau. `backend/tests/` không thuộc `root_packages` nên `flows/` được import mọi factory. Xem `docs/architecture/12-testing-strategy.md` mục 4.
- Trong contract `forbidden` "Module khác chỉ được dùng contracts và events" (và trong `scripts/gen_importlinter.py`), đặt `allow_indirect_imports = true`. Mặc định import-linter cấm cả chuỗi gián tiếp, nên mọi lời gọi hợp lệ `ordering.services → inventory.contracts → inventory.services → inventory.models` đều bị báo lỗi. Xem `docs/architecture/02-backend-structure.md` mục 8.
- Không dùng `ignore_imports` cho `modules.*.tests.**`: test kiểm tra dữ liệu của module khác qua `contracts`, không import `models` của module đó.
- Viết test cho cấu hình: mỗi acceptance criteria dưới đây có một file Python mẫu, chạy `lint-imports` và kiểm tra kết quả.

## Acceptance criteria

- [ ] Test của `inventory` import `modules.ordering.tests.factories` thì `lint-imports` báo lỗi.
- [ ] Test của `payments` import `modules.shipping.tests.factories` thì `lint-imports` báo lỗi.
- [ ] Test của `ordering` import `modules.inventory.tests.factories` thì `lint-imports` qua.
- [ ] Test của `ordering` import `modules.inventory.models` thì `lint-imports` báo lỗi.
- [ ] `modules.ordering.services` gọi `modules.inventory.contracts` thì `lint-imports` qua.
- [ ] Code ngoài `tests` vẫn không được import trực tiếp `models`, `services`, `selectors`, `api` của module khác.
