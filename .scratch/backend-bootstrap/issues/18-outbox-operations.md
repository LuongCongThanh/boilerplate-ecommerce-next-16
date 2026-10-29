# Lệnh vận hành và theo dõi outbox

Status: ready-for-agent

Blocked by: 10

Spec: [spec.md](../spec.md)

Tách từ ticket [10](./10-shared-events-outbox.md).

## Việc cần làm

Theo [07 mục 3](../../../docs/architecture/07-async-events-jobs.md):

- `delivery_lag()`, `get_delivery_outcomes(event_id, handler_names)`.
- Job `purge_old_outbox_events`, đăng ký lịch trong `config/celery.py`.
- Lệnh `retry_failed_events` và `replay_events`.

## Acceptance criteria

- [ ] `retry_failed_events` mở lại delivery `failed` và lần chạy sau thành công.
- [ ] Purge không xoá sự kiện còn delivery `pending` hoặc `failed`.
- [ ] `get_delivery_outcomes` trả đúng trạng thái của từng handler được hỏi.
- [ ] Các kịch bản ở [07 mục 5](../../../docs/architecture/07-async-events-jobs.md#5-kịch-bản-kiểm-thử) về lệnh vận hành và purge đều có test.
