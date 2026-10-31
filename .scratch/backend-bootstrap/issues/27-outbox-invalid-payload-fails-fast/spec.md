# Payload không còn hợp lệ với class sự kiện thì delivery `failed` ngay

Status: needs-triage

Spec: [spec.md](../../spec.md)

Tách từ review của ticket [10](../10-shared-events-outbox/spec.md) ngày 30/10/2026 (finding B7).

## Bối cảnh

Consumer parse payload bằng `model_validate` của class sự kiện. Nếu ai đó thêm field bắt buộc vào `…V1` (trái quy tắc nâng version ở [07 mục 2](../../../../docs/architecture/07-async-events-jobs.md#2-danh-mục-sự-kiện)), mọi sự kiện cũ trong outbox ném `pydantic.ValidationError` giống nhau ở mọi lần. Theo bảng 07 mục 1.3, đây là "Exception khác" nên retry 5 lần (khoảng 51 phút) rồi mới `failed`, kèm traceback mỗi lần.

## Việc cần làm

- Quyết định: `ValidationError` khi parse payload chuyển `failed` ngay (cần người vận hành) thay vì retry; sửa bảng ở 07 mục 1.3.

## Acceptance criteria

- [ ] Payload không parse được bằng class sự kiện thì delivery chuyển `failed` ở lần đầu, có `failed_at`, `last_error`, log `ERROR`.
- [ ] Lỗi trong handler (sau khi parse thành công) vẫn theo lịch retry cũ.
