# Gom chuyển trạng thái delivery và helper test của outbox

Status: ready-for-agent

Spec: [spec.md](../../spec.md)

Tách từ review của ticket [10](../10-shared-events-outbox/spec.md) ngày 30/10/2026 (finding T5, T6, T8, T9, T11). Không đổi hành vi.

## Việc cần làm

- Chuyển `completed`/`rejected`/retry/`failed` của `EventDelivery` (hiện là `_reject`, `_schedule_retry` trong `shared/events/consumer.py`) thành method trên model, để `retry_failed_events` của ticket [18](../18-outbox-operations/spec.md) dùng chung.
- Gom điều kiện "delivery tới hạn" (đang viết bằng Python trong consumer và bằng ORM trong relay) về một QuerySet method, ví dụ `EventDelivery.objects.due(now)`.
- Cân nhắc abstract model chung cho `id` UUID v7 (`BaseModel`, `OutboxEvent`, `EventDelivery` đang khai báo lặp).
- Test: gom `NOW`, `ORDER_CODE`, exception giả, helper ghi tác động và khung thread + `Barrier` vào `shared/events/tests/conftest.py`.
- `OutboxEventFactory` không mặc định trỏ tới sự kiện mẫu chỉ khai báo trong test (`shared.sample-happened`).
- Từ review ticket [18](../18-outbox-operations/spec.md) (T6, T7, B10): gom helper `_listed_event` (lặp ở `test_purge.py`, `test_replay_events.py`, `test_selectors.py`) và `_failed` (`test_retry_failed_events.py`) thành trait của factory, ví dụ `OutboxEventFactory(listed=True)`. Điều kiện "delivery tới hạn" có thêm bản thứ ba ở `shared/events/selectors.py` (`delivery_lag`); `delivery_lag` cố ý không xét `next_dispatch_at`, nên QuerySet method phải tách hai điều kiện.

## Acceptance criteria

- [ ] Các hạng mục trên làm xong, `make lint` và `make test` vẫn xanh, không đổi test nào về hành vi.
