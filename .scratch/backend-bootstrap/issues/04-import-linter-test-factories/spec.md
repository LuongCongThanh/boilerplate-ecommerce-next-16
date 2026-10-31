# `gen_importlinter.py` và ranh giới `import-linter` cho test và factory

Status: ready-for-agent

Blocked by: 07

Spec: [spec.md](../../spec.md)

## Việc cần làm

- `scripts/gen_importlinter.py` sinh contract `forbidden` cho mọi cặp module và có chế độ `--check` (02 mục 8). Contract `layers` đã có trong `pyproject.toml` từ ticket 07. Thêm `gen_importlinter.py --check` vào `make lint` và bước Lint của job `backend` trong `.github/workflows/ci.yml`.
- Không thêm contract riêng cho factory. Contract `layers` đã chặn test của module lớp dưới import factory của module lớp trên, và chặn hai module cùng lớp import lẫn nhau. `backend/tests/` không thuộc `root_packages` nên `flows/` được import mọi factory. Xem `docs/architecture/12-testing-strategy.md` mục 4.
- Trong contract `forbidden` "Module khác chỉ được dùng contracts và events" (và trong `scripts/gen_importlinter.py`), đặt `allow_indirect_imports = true`. Mặc định import-linter cấm cả chuỗi gián tiếp, nên mọi lời gọi hợp lệ `ordering.services → inventory.contracts → inventory.services → inventory.models` đều bị báo lỗi. Xem `docs/architecture/02-backend-structure.md` mục 8.
- Không dùng `ignore_imports` cho `modules.*.tests.**`: test kiểm tra dữ liệu của module khác qua `contracts`, không import `models` của module đó.
- Viết test cho cấu hình: mỗi acceptance criteria dưới đây có một file Python mẫu, chạy `lint-imports` và kiểm tra kết quả.

## Acceptance criteria

- [ ] Sửa tay contract `forbidden` trong `pyproject.toml` thì `gen_importlinter.py --check` báo lệch, cả ở `make lint` lẫn CI.
- [ ] Test của `inventory` import `modules.ordering.tests.factories` thì `lint-imports` báo lỗi.
- [ ] Test của `payments` import `modules.shipping.tests.factories` thì `lint-imports` báo lỗi.
- [ ] Test của `ordering` import `modules.inventory.tests.factories` thì `lint-imports` qua.
- [ ] Test của `ordering` import `modules.inventory.models` thì `lint-imports` báo lỗi.
- [ ] `modules.ordering.services` gọi `modules.inventory.contracts` thì `lint-imports` qua.
- [ ] Code ngoài `tests` vẫn không được import trực tiếp `models`, `services`, `selectors`, `api` của module khác.
