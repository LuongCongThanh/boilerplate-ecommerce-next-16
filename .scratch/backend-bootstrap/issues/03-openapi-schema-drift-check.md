# Commit `openapi.yaml` và chặn schema lệch trong CI

Status: needs-triage

## Việc cần làm

- Làm sau khi backend có endpoint đầu tiên.
- Sinh schema bằng `manage.py spectacular --validate --file openapi.yaml` và commit tại `backend/openapi.yaml`.
- Thêm lệnh `make openapi` để sinh lại schema.
- Thêm bước vào job `backend` của `.github/workflows/ci.yml`: sinh schema ra file tạm, so với `backend/openapi.yaml`, fail nếu khác và in hướng dẫn chạy `make openapi`.
- Xem `docs/architecture/12-testing-strategy.md` mục 5.

## Acceptance criteria

- [ ] PR đổi API mà không cập nhật `backend/openapi.yaml` bị CI chặn.
- [ ] `--validate` báo lỗi schema thì CI cũng fail.
