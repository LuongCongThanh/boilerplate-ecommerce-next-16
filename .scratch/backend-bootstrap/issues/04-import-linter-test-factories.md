# Contract `import-linter` cho factory trong test

Status: needs-triage

## Việc cần làm

- Thêm contract để test của một module chỉ import `tests.factories` của chính nó và của module lớp dưới; `backend/tests/flows/` được import mọi factory. Xem `docs/architecture/12-testing-strategy.md` mục 4.
- Cần kiểm tra cách contract này sống chung với contract "Module khác chỉ được dùng contracts và events" (`docs/architecture/02-backend-structure.md` mục 8): factory của `inventory` import `modules.inventory.models`, nên test của `ordering` import factory đó sẽ tạo đường import gián tiếp tới model của module khác. Có thể phải dùng `ignore_imports` cho `modules.*.tests.**`, hoặc bỏ `modules.*.tests` khỏi phạm vi contract đó.

## Acceptance criteria

- [ ] Test của `inventory` import `modules.ordering.tests.factories` thì `lint-imports` báo lỗi.
- [ ] Test của `ordering` import `modules.inventory.tests.factories` thì `lint-imports` qua.
- [ ] Code ngoài `tests` vẫn không được import model của module khác.
