# Phase 2 — code bằng TDD

Full: một sub-agent cho mỗi slice, theo thứ tự DAG (`dependsOn` xong hết mới bắt đầu). Lite: phiên chính làm một slice.

## Trong một slice

1. `state.py set <T> slices.<id>.status=code currentSlice=<id>`.
2. `mattpocock-skills:tdd`, chỉ test ở seam của slice. Mỗi vòng: viết một test, chạy `uv run pytest <file>::<test> -x` trong `backend/` và thấy nó _red_ đúng lý do (assert sai, không phải lỗi import), viết code tối thiểu cho _green_, lặp lại.
3. Test đỏ không thuộc slice → chứng minh nó đỏ trên `origin/dev` (`reference/rules.md` → *Test*), ghi `notes`, làm tiếp.
4. Cần migration → `uv run python manage.py makemigrations <app>` và đọc lại file sinh ra; migration phải đảo ngược được (`docs/architecture/12-testing-strategy.md` mục 6).
5. Cuối slice: `uv run ruff format` và `uv run ruff check --fix` cho file đã đổi, chạy lại các test của slice.
6. Commit: `git add -- <đường dẫn cụ thể>`, message theo `templates/commit-msg.md`.
7. `state.py set <T> slices.<id>.status=done 'slices.<id>.tests=[…]' 'slices.<id>.handoff=[…]' 'next=…'`. Tên test đổi so với kế hoạch thì ghi tên thật.
8. Sub-agent trả về theo `reference/sub-agent.md`. Phiên chính in điểm clear rồi giao slice tiếp theo.

## Cuối phase

```bash
python S/scripts/run_logged.py --label lint --cwd backend -- make lint
python S/scripts/run_logged.py --label test --cwd backend -- make test
python S/scripts/check_ac_trace.py <T>
python S/scripts/state.py transition <T> --to report --next "viết báo cáo" --reason "mọi slice xanh"
```

Đỏ → sửa trong phạm vi ticket rồi chạy lại; đỏ ngoài phạm vi → *Cần người dùng*.

## Xong khi

Mọi slice `done`; `make lint`, `make test`, `check_ac_trace.py` xanh; mọi slice đã commit; `phase` là `report`.
