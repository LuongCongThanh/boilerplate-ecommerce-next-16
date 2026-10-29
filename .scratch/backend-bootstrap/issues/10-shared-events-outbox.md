# Sự kiện qua outbox: publisher, relay, consumer và retry

Status: ready-for-agent

Blocked by: 09, 15

Spec: [spec.md](../spec.md)

Các lệnh vận hành và hàm theo dõi tách sang ticket [18](./18-outbox-operations.md).

## Việc cần làm

Làm đúng [07 mục 1 và 3](../../../docs/architecture/07-async-events-jobs.md) và [ADR 0007](../../../docs/adr/0007-events-outbox-celery-no-kafka.md):

- Model `OutboxEvent`, `EventDelivery` theo [03 mục 1.3–1.4](../../../docs/architecture/03-data-model.md#13-shared_outbox_event-sự-kiện-chờ-phát).
- `DomainEvent` (pydantic), `publish()` ghi outbox trong transaction hiện tại, decorator `@handles(event_type, version)`.
- Relay (`manage.py run_outbox_relay`): lập delivery cho từng handler, giao các delivery `pending` tới hạn qua Celery, `FOR UPDATE SKIP LOCKED`, chạy hai bản cùng lúc vẫn an toàn. Thêm service `relay` vào `docker-compose.yml` ([08 mục 7](../../../docs/architecture/08-local-development.md#7-docker-composeyml-rút-gọn)).
- Consumer: khoá delivery, chạy handler trong savepoint, chuyển `completed`/`rejected`/`failed` cùng transaction với tác động DB; `RetryLater` và lịch retry lưu trong DB.
- `shared.tasks.enqueue_on_commit`.
- `shared.testing.events.drain_events()` cho flow test.

## Acceptance criteria

- [ ] Một sự kiện mẫu có hai handler: mỗi handler chạy đúng một lần dù task bị giao lặp.
- [ ] Transaction ghi sự kiện bị rollback thì không có delivery nào được tạo.
- [ ] Handler ném `RetryLater` thì delivery giữ `pending` với `next_attempt_at` theo lịch retry; hết retry thì `failed` có `failed_at`, `last_error`.
- [ ] Handler lỗi không làm hỏng tác động DB của handler khác cùng sự kiện.
- [ ] Redis mất task sau khi đã nhận thì relay giao lại khi tới `next_dispatch_at`.
- [ ] `make up` bật cả `relay`, và service này không khởi động lại liên tục.
- [ ] Các kịch bản ở [07 mục 5](../../../docs/architecture/07-async-events-jobs.md#5-kịch-bản-kiểm-thử) về publish, relay, consumer và retry đều có test.
