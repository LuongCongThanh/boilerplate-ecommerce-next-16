# Delivery bị kill do time limit được giao lại vô hạn

Status: needs-triage

Spec: [spec.md](../spec.md)

Tách từ review của ticket [10](./10-shared-events-outbox.md) ngày 30/10/2026 (finding B3).

## Bối cảnh

[07 mục 1.3](../../../docs/architecture/07-async-events-jobs.md#13-retry-và-lỗi) quy định `attempts` chỉ đếm lỗi handler đã lưu được; task bị mất không tiêu lượt retry. Handler chạy quá `CELERY_TASK_TIME_LIMIT` (120 giây) hoặc làm worker hết bộ nhớ thì process bị kill trước khi consumer kịp lưu lỗi: transaction rollback, delivery giữ `pending` với `attempts` cũ, relay giao lại sau `REDISPATCH_AFTER` (3 phút), lại bị kill. Vòng này lặp vô hạn, không bao giờ chuyển `failed` nên không có cảnh báo Sentry (`event_delivery_failed`).

## Việc cần làm

- Chọn cách chặn: đếm số lần giao (`dispatch_count` hoặc dùng `last_dispatched_at`) và chuyển `failed` khi vượt ngưỡng, hoặc `soft_time_limit` để consumer bắt `SoftTimeLimitExceeded` và lưu như lỗi handler.
- Sửa 07 mục 1.3 và 03 mục 1.4 nếu thêm cột hoặc đổi quy tắc "task bị mất không tiêu lượt retry".

## Acceptance criteria

- [ ] Handler luôn vượt time limit thì delivery cuối cùng chuyển `failed` và có log `ERROR`, không giao lại vô hạn.
- [ ] Task mất do Redis (không phải do handler) vẫn không tiêu lượt retry.
