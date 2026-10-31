# Payload không còn hợp lệ với class sự kiện thì delivery `failed` ngay

Status: ready-for-agent

Spec: [spec.md](../../spec.md)

Tách từ review của ticket [10](../10-shared-events-outbox/spec.md) ngày 30/10/2026 (finding B7).

## Bối cảnh

Consumer parse payload bằng `model_validate` của class sự kiện. Nếu ai đó thêm field bắt buộc vào `…V1` (trái quy tắc nâng version ở [07 mục 2](../../../../docs/architecture/07-async-events-jobs.md#2-danh-mục-sự-kiện)), mọi sự kiện cũ trong outbox ném `pydantic.ValidationError` giống nhau ở mọi lần. Theo bảng 07 mục 1.3, đây là "Exception khác" nên retry 5 lần (khoảng 51 phút) rồi mới `failed`, kèm traceback mỗi lần.

## Việc cần làm

- Quyết định: `ValidationError` khi parse payload chuyển `failed` ngay (cần người vận hành) thay vì retry; sửa bảng ở 07 mục 1.3.

## Quyết định

Chốt khi grilling ngày 01/11/2026.

| Chủ đề | Quyết định |
|---|---|
| Tài liệu chi phối | `backend/shared/events/consumer.py` → 07 §1.1.1, §1.3; 03 §1.4 (`last_error` và log không mang message vì có thể chứa PII). `backend/shared/events/tests/test_consumer.py` → 02 §9.2 (tên file test), 02 §9.5 (factory), 12. `docs/architecture/07-async-events-jobs.md` §1.3 sửa bảng trong cùng PR. |
| Chỗ parse payload | Chuyển `model_validate` từ transaction 2 lên transaction 1, sau khi tra handler và class sự kiện, trước khi kiểm `interrupted_runs` và trước khi tăng bộ đếm. Parse là hàm thuần nên không cần savepoint. Parse lỗi thì handler không chạy, nên không tính là lần chạy dở và `attempts` giữ nguyên (07 §1.3: `attempts` chỉ đếm lỗi handler đã lưu được). Kiểm parse trước `interrupted_runs` để `last_error` ghi đúng nguyên nhân gốc. |
| Phạm vi bắt lỗi | Chỉ `pydantic.ValidationError` ném ra từ bước parse mới chuyển `failed` ngay. `ValidationError` ném trong handler (ví dụ handler tự parse dữ liệu ngoài) vẫn là "Exception khác" và retry theo lịch (AC2). |
| `last_error` | `describe_error(exc)` như các nhánh khác, nên giá trị là `"ValidationError"`; không thêm hằng số mới. |
| Log | Một log `ERROR` `event_delivery_failed` qua `_mark_failed` (Sentry cảnh báo như khi hết retry), kèm `invalid_fields`: danh sách `{loc, type}` lấy từ `exc.errors(include_input=False)`. Bỏ `msg` và input để không lọt PII. Không thêm log thứ hai để Sentry không cảnh báo hai lần cho cùng một delivery. |
| Mở lại | Không đổi `retry_failed_events`: người vận hành sửa class sự kiện (hoặc thêm version) rồi chạy lệnh như với delivery `failed` khác. |

## Acceptance criteria

- [ ] Payload không parse được bằng class sự kiện thì delivery chuyển `failed` ở lần đầu, có `failed_at`, `last_error`, log `ERROR`.
- [ ] Lỗi trong handler (sau khi parse thành công) vẫn theo lịch retry cũ.
