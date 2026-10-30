# Sự kiện qua outbox: publisher, relay, consumer và retry

Status: resolved

**PR:** #36

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

## Quyết định

Chốt khi grilling ngày 30/10/2026.

| Chủ đề | Quyết định |
|---|---|
| Tài liệu chi phối | `shared/events/models.py`, `shared/migrations/0003_*`, `shared/models.py`: 03 §1.3–1.4, 02 §9.1 (khoá chính), §9.2 (tên bảng), ADR 0007, ADR 0008. `shared/events/base.py`, `publisher.py`, `registry.py`, `__init__.py`: 07 §1, §2 (version, payload không PII), 02 §5 (cây `shared/events/`), §9.2 (tên class sự kiện, `event_type`). `shared/events/relay.py`, `management/commands/run_outbox_relay.py`: 07 §1.1.1, §1.3. `shared/events/consumer.py`, `shared/events/tasks.py`: 07 §1.1.1, §1.3, §3.1 (queue `events`), 02 §9.2 (tên Celery task). `shared/tasks.py`: 02 §9.1 (*Việc ra ngoài DB*), 07 §1.3. `shared/testing/events.py`: 12 §2.7, 02 §9.5. `config/celery.py`, `config/settings/base.py`: 07 §3.1, §3.3, 02 §5 (`autodiscover_tasks`). `docker-compose.yml`, `Makefile`: 08 §7. Test: 07 §5, 12 §2.2, §2.3, 02 §9.2 (tên file test), §9.5 (factory, time-machine) |
| Model | `OutboxEvent` (`shared_outbox_event`) và `EventDelivery` (`shared_event_delivery`) đúng cột, `CHECK`, `UNIQUE`, partial index của 03 §1.3–1.4. Kế thừa `models.Model`, không kế thừa `BaseModel`: 03 không có `created_at`/`updated_at` cho hai bảng này. `OutboxEvent.id` UUID PK `default=uuid7` (= `event_id`); `EventDelivery` có `id` UUID v7 riêng (ADR 0008), FK `event` `db_column="event_id"` `CASCADE`. `status` là `TextChoices` `pending/completed/rejected/failed`. `shared/models.py` import hai model như với `geo` |
| `DomainEvent` | pydantic `BaseModel` frozen trong `shared/events/base.py`: `event_id` (UUID v7), `occurred_at`, `correlation_id: str \| None` (lấy `request_id` từ contextvars của structlog nếu có); class con khai báo `event_type: ClassVar[str]`, `schema_version: ClassVar[int]`. `__init_subclass__` đăng ký class theo `(event_type, schema_version)`, trùng thì ném lỗi khi import. Payload lưu là `model_dump(mode="json")` trừ `event_id`, `occurred_at` (đã là cột) |
| `publish()` | `shared.events.publish(event)` ghi `OutboxEvent` trong transaction hiện tại; không tự mở transaction, gọi ngoài `transaction.atomic` thì ném `RuntimeError` (thêm khi review, B4). `EventPublisher` là class trong `publisher.py`, `publish` là hàm gọi instance mặc định (chỗ cắm adapter Kafka ở ADR 0007) |
| `@handles` | `@handles(event_type, version=1, name="<module>.<snake_case>")`: `name` bắt buộc, là cột `handler` của delivery, ổn định khi đổi tên file/hàm (giống tên Celery task, 02 §9.2). Trùng `name` hoặc `name` dài quá 100 ký tự (`HANDLER_NAME_MAX_LENGTH`, cột `handler`) ném lỗi khi import (độ dài thêm khi review, B10). `shared.events.registry.autodiscover(package)` nạp `events.py`, `handlers.py` của package con; `ModulesConfig.ready()` gọi `autodiscover("modules")` theo 02 §5 (thêm khi review, B1). Handler nhận instance của class sự kiện đã parse từ payload. Registry ở `registry.py` |
| Relay | `relay.create_deliveries(batch=100)`: khoá `OutboxEvent` chưa có `deliveries_created_at` bằng `select_for_update(skip_locked=True)`, tạo delivery cho mọi handler đăng ký (`bulk_create(ignore_conflicts=True)` trên `UNIQUE(event_id, handler)`), ghi `deliveries_created_at`, cùng transaction; không có handler thì vẫn ghi marker và log `outbox_event_no_handlers`. `relay.dispatch_due(batch=100)`: khoá delivery `pending` có `next_attempt_at ≤ now` và `next_dispatch_at ≤ now` (skip locked), đặt `next_dispatch_at = now + 3 phút`, `last_dispatched_at = now`, commit, rồi mới `dispatch_event.apply_async(...)` (queue `events` do decorator của task định tuyến); chỉ bắt `kombu` `OperationalError`: dừng cả lô ở lỗi đầu, log `WARNING` `outbox_dispatch_failed` kèm `deferred`, các delivery giữ hạn đã lưu; lỗi khác ném ra (07 §1.3, thêm khi review, B5/T3). `run_outbox_relay` lặp hai hàm mỗi 1 giây, mỗi hàm `try` riêng để lỗi bước đầu không chặn bước sau (thêm khi review, B2), dừng sạch khi nhận SIGTERM/SIGINT, có `--once` cho test. Sentry Cron check-in (07 §3.4) chưa làm: Sentry chưa cấu hình ở M0 |
| Consumer | `consumer.process_delivery(event_id, handler_name)` trong `transaction.atomic`: khoá delivery (`select_for_update`, chờ khoá); bỏ qua nếu không còn `pending` hoặc `next_attempt_at > now`. Handler chạy trong savepoint. Kết thúc bình thường → `completed`, `completed_at`. `DomainError` → `rejected`, log `WARNING` `event_rejected` với `event_type`, `handler`, `code`. `RetryLater` hoặc `Exception` khác → `attempts += 1`, `last_error`, `next_attempt_at = next_dispatch_at = now + lịch[attempts-1]` (`now` lấy sau khi handler chạy, cũng dùng cho `completed_at`, `failed_at`; thêm khi review, B8); khi `attempts > 5` → `failed`, `failed_at`, log `ERROR` `event_delivery_failed` (Sentry bắt log ERROR). `DatabaseError` ngoài savepoint không bắt, để toàn transaction rollback (07 §1.3). Handler không có trong registry → giữ `pending`, log `ERROR` `event_handler_missing`, không tăng `attempts` |
| Lịch retry | Hằng `RETRY_DELAYS = (10s, 1m, 5m, 15m, 30m)` trong `consumer.py` (07 §1.3); hết 5 lần retry sau lần đầu → `failed` |
| `last_error` | Chỉ tên class và `code` nếu có, ví dụ `InvalidTransition(INVALID_TRANSITION)`, cắt 500 ký tự; không ghi message để không lọt PII (03 §1.4). Traceback đầy đủ đi qua `logger.exception` |
| Celery task | `shared.events.tasks.dispatch_event(event_id, handler_name)`, `name="shared.dispatch_event"`, queue `events`; chỉ gọi `process_delivery`. `config/celery.py` autodiscover thêm `shared.events` |
| Cấu hình Celery (yêu cầu thêm) | `config/settings/base.py` thêm 07 §3.3: `CELERY_TASK_ACKS_LATE`, `CELERY_TASK_REJECT_ON_WORKER_LOST`, `CELERY_WORKER_PREFETCH_MULTIPLIER = 1`, `CELERY_TASK_TIME_LIMIT = 120`, `CELERY_TASK_IGNORE_RESULT`. Người dùng yêu cầu ngày 30/10/2026: hạn giao lại 3 phút dựa vào time limit 120 giây |
| `enqueue_on_commit` | `shared.tasks.enqueue_on_commit(task_name, **kwargs)`: `transaction.on_commit(..., robust=True)` gọi `app.tasks[task_name].apply_async(kwargs=kwargs)`. Lấy task theo tên trong registry của app (không `send_task`) để `CELERY_TASK_ALWAYS_EAGER` của test có hiệu lực và tên sai lộ ra ngay. Không dùng `apply_async_on_commit` của Celery vì nó cần object task, mà code nghiệp vụ chỉ biết tên |
| `drain_events()` | `shared/testing/events.py`: chạy callback `on_commit` đang chờ trên kết nối hiện tại, rồi lặp `create_deliveries` + `dispatch_due` (Celery eager nên handler chạy ngay) tới khi không còn sự kiện chưa lập danh sách và không còn delivery tới hạn; giới hạn 100 vòng rồi ném lỗi để tránh lặp vô hạn |
| Compose | Service `relay` (`<<: *app`, `command: python manage.py run_outbox_relay`) như 08 §7; `make restart-worker` khởi động lại cả `relay` |
| Test | `shared/events/tests/` theo 07 §5: `test_publisher.py`, `test_relay.py`, `test_consumer.py`, `test_drain.py`; `shared/tests/test_tasks.py` cho `enqueue_on_commit`. Sự kiện và handler mẫu khai báo trong `shared/events/tests/conftest.py`, registry được khôi phục sau mỗi test; tác động DB của handler ghi vào model test tạo bằng `schema_editor` như `shared/tests/test_models.py`. Giao trùng đồng thời và hai relay cùng chạy: `django_db(transaction=True)` + thread + `threading.Barrier` trên PostgreSQL thật (12 §2.2); marker `concurrency` để ticket [02](./02-pytest-markers-and-br-report.md) khai báo. Thời gian cố định bằng `time-machine`. `backend/tests/test_event_payloads.py` (07 §5) làm ở ticket này: hiện chưa có sự kiện thật, test kiểm hàm dò tên field cấm trên class mẫu và chạy trên mọi class đã đăng ký |
| Ngoài phạm vi | `delivery_lag`, `get_delivery_outcomes`, purge, `retry_failed_events`, `replay_events`: ticket [18](./18-outbox-operations.md). Sentry Cron check-in của relay: khi cấu hình Sentry |

## Kế hoạch

Sinh bằng `plan.py` từ state của skill. Mỗi task là đúng một commit có trailer `Task: <task>`.

| Task | AC | Seam | Test dự kiến | File | Sau |
| --- | --- | --- | --- | --- | --- |
| S1 | 7 | shared.events.publish() trong transaction; registry @handles; DomainEvent | `shared/events/tests/test_publisher.py::test_publish_writes_outbox_row_in_current_transaction`<br>`shared/events/tests/test_publisher.py::test_publish_rolled_back_with_transaction`<br>`shared/events/tests/test_publisher.py::test_handles_rejects_duplicate_name`<br>`shared/events/tests/test_publisher.py::test_duplicate_event_class_rejected`<br>`tests/test_event_payloads.py::test_registered_event_payloads_have_no_pii`<br>`tests/test_event_payloads.py::test_forbidden_field_names_detected` | `backend/shared/events/__init__.py`<br>`backend/shared/events/base.py`<br>`backend/shared/events/models.py`<br>`backend/shared/events/publisher.py`<br>`backend/shared/events/registry.py`<br>`backend/shared/models.py`<br>`backend/shared/migrations/0003_outbox.py`<br>`backend/shared/events/tests/__init__.py`<br>`backend/shared/events/tests/conftest.py`<br>`backend/shared/events/tests/test_publisher.py`<br>`backend/tests/test_event_payloads.py` | — |
| S2 | 3, 4, 7 | consumer.process_delivery(event_id, handler_name) và task shared.dispatch_event | `shared/events/tests/test_consumer.py::test_success_commits_effect_and_completed`<br>`shared/events/tests/test_consumer.py::test_retry_later_keeps_pending_with_schedule`<br>`shared/events/tests/test_consumer.py::test_exception_rolls_back_handler_and_schedules_retry`<br>`shared/events/tests/test_consumer.py::test_exhausted_retries_mark_failed`<br>`shared/events/tests/test_consumer.py::test_domain_error_rejects_without_retry`<br>`shared/events/tests/test_consumer.py::test_failing_handler_does_not_affect_other_handler`<br>`shared/events/tests/test_consumer.py::test_skips_finished_delivery`<br>`shared/events/tests/test_consumer.py::test_skips_before_next_attempt_at`<br>`shared/events/tests/test_consumer.py::test_concurrent_duplicate_dispatch_commits_once` | `backend/shared/events/consumer.py`<br>`backend/shared/events/tasks.py`<br>`backend/config/celery.py`<br>`backend/config/settings/base.py`<br>`backend/shared/events/tests/test_consumer.py` | S1 |
| S3 | 2, 5, 6, 7 | relay.create_deliveries(), relay.dispatch_due(), manage.py run_outbox_relay --once | `shared/events/tests/test_relay.py::test_rolled_back_publish_creates_no_delivery`<br>`shared/events/tests/test_relay.py::test_create_deliveries_one_per_handler_with_marker`<br>`shared/events/tests/test_relay.py::test_event_without_handlers_gets_marker`<br>`shared/events/tests/test_relay.py::test_two_relays_concurrently_create_no_duplicates`<br>`shared/events/tests/test_relay.py::test_lost_task_redispatched_after_deadline`<br>`shared/events/tests/test_relay.py::test_broker_error_keeps_delivery_for_later`<br>`shared/events/tests/test_relay.py::test_dispatch_skips_retry_not_due`<br>`shared/events/tests/test_relay.py::test_run_outbox_relay_once` | `backend/shared/events/relay.py`<br>`backend/shared/management/commands/run_outbox_relay.py`<br>`backend/docker-compose.yml`<br>`backend/Makefile`<br>`backend/shared/events/tests/test_relay.py` | S2 |
| S4 | 1 | shared.tasks.enqueue_on_commit(); shared.testing.events.drain_events() | `shared/events/tests/test_drain.py::test_two_handlers_each_run_once_on_duplicate_dispatch`<br>`shared/events/tests/test_drain.py::test_drain_does_not_wait_for_future_retry`<br>`shared/tests/test_tasks.py::test_enqueue_on_commit_runs_after_commit`<br>`shared/tests/test_tasks.py::test_enqueue_on_commit_skipped_on_rollback`<br>`shared/tests/test_tasks.py::test_enqueue_on_commit_broker_error_is_logged` | `backend/shared/tasks.py`<br>`backend/shared/testing/events.py`<br>`backend/shared/events/tests/test_drain.py`<br>`backend/shared/tests/test_tasks.py` | S3 |

AC 6 không test tự động: cần Docker thật; kiểm tay: make up, rồi docker compose ps sau 1 phút thấy relay Up không restart, make logs s=relay có vòng lặp chạy

Commit dự kiến: `plan` → `S1` → `S2` → `S3` → `S4` → `R1 (khi review cần sửa)` → `sync` → `close`.

## Acceptance criteria

- [x] Một sự kiện mẫu có hai handler: mỗi handler chạy đúng một lần dù task bị giao lặp.
- [x] Transaction ghi sự kiện bị rollback thì không có delivery nào được tạo.
- [x] Handler ném `RetryLater` thì delivery giữ `pending` với `next_attempt_at` theo lịch retry; hết retry thì `failed` có `failed_at`, `last_error`.
- [x] Handler lỗi không làm hỏng tác động DB của handler khác cùng sự kiện.
- [x] Redis mất task sau khi đã nhận thì relay giao lại khi tới `next_dispatch_at`.
- [x] `make up` bật cả `relay`, và service này không khởi động lại liên tục.
- [x] Các kịch bản ở [07 mục 5](../../../docs/architecture/07-async-events-jobs.md#5-kịch-bản-kiểm-thử) về publish, relay, consumer và retry đều có test.

## Comments

### Báo cáo 30/10/2026

**Nhánh:** `feat/shared-outbox` · **PR:** #36 · **Mode:** full

#### Đã làm

| AC | Bằng chứng |
| --- | --- |
| 1. Hai handler, mỗi handler chạy đúng một lần dù task giao lặp | `shared/events/tests/test_drain.py::test_two_handlers_each_run_once_on_duplicate_dispatch`, `shared/events/tests/test_consumer.py::test_concurrent_duplicate_dispatch_commits_once` (PostgreSQL thật, hai thread) |
| 2. Rollback transaction ghi sự kiện thì không có delivery | `shared/events/tests/test_relay.py::test_rolled_back_publish_creates_no_delivery`, `shared/events/tests/test_publisher.py::test_publish_rolled_back_with_transaction` |
| 3. `RetryLater` giữ `pending` theo lịch; hết retry thì `failed` | `shared/events/tests/test_consumer.py::test_retry_later_keeps_pending_with_schedule`, `::test_exhausted_retries_mark_failed` |
| 4. Handler lỗi không làm hỏng tác động DB của handler khác | `shared/events/tests/test_consumer.py::test_failing_handler_does_not_affect_other_handler` |
| 5. Redis mất task thì relay giao lại khi tới `next_dispatch_at` | `shared/events/tests/test_relay.py::test_lost_task_redispatched_after_deadline`, `::test_broker_error_keeps_delivery_for_later` |
| 6. `make up` bật `relay`, không khởi động lại liên tục | Phần code: `shared/events/tests/test_relay.py::test_run_outbox_relay_survives_iteration_error` (vòng 1 lỗi, vòng 2 vẫn giao được; lỗi ở `create_deliveries` không chặn `dispatch_due`). Kiểm tay 30/10/2026: `make up` trên Windows + Docker Desktop, sau hơn 1 phút `docker compose ps` thấy `relay` Up, `RestartCount=0`, log có `outbox_relay_started`, không có lỗi (không test tự động: cần Docker thật) |
| 7. Kịch bản 07 §5 về publish, relay, consumer, retry có test | Publish: `test_publisher.py` (4 test), `tests/test_event_payloads.py` (2 test). Consumer: `test_consumer.py` (10 test: completed, RetryLater, exception, failed, rejected, bỏ qua delivery đã kết thúc / chưa tới hạn, thiếu handler, giao trùng đồng thời). Relay: `test_relay.py` (9 test: lập danh sách nguyên tử, sự kiện không có handler, hai relay đồng thời, mất task, lỗi broker, retry chưa tới hạn, lệnh `--once`). `enqueue_on_commit`: `shared/tests/test_tasks.py` (4 test). `drain_events`: `test_drain.py` (4 test) |

`make lint` xanh (ruff, mypy, import-linter 1 kept / 0 broken) · `make test`: 212 passed trong 12.77s

#### Chưa làm

- Relay dừng sạch khi nhận SIGTERM/SIGINT: có code, chưa có test tự động.
- `delivery_lag`, `get_delivery_outcomes`, purge, `retry_failed_events`, `replay_events`: thuộc ticket [18](./18-outbox-operations.md).
- Sentry Cron check-in của relay (07 §3.4): chờ cấu hình Sentry.

#### Gap

- Test giao trùng đồng thời và hai relay đồng thời chưa gắn marker `concurrency` (12 §2.2); ticket [02](./02-pytest-markers-and-br-report.md) khai báo marker rồi gắn.
- Máy dev Windows bật Smart App Control chặn `.pyd` không ký của mypy compiled; đã cài mypy 2.4.1 dạng pure Python (`uv pip install --reinstall-package mypy --no-binary mypy "mypy==2.4.1"`). Nâng mypy hoặc tạo lại `.venv` phải cài lại. Repo chưa cài hook pre-commit trên máy này.
- `last_error` chỉ ghi tên class và `code`; người vận hành cần traceback thì xem log/Sentry.

#### Thay đổi theo yêu cầu

- 30/10/2026: thêm cấu hình Celery 07 §3.3 vào `config/settings/base.py` (`CELERY_TASK_ACKS_LATE`, `CELERY_TASK_REJECT_ON_WORKER_LOST`, `CELERY_WORKER_PREFETCH_MULTIPLIER = 1`, `CELERY_TASK_TIME_LIMIT = 120`, `CELERY_TASK_IGNORE_RESULT`), commit S2.
- 30/10/2026, SonarCloud `models.py:70` (field `status` trùng tên khác hoa/thường với alias `EventDelivery.Status`): bỏ alias, code và test dùng thẳng `DeliveryStatus`; không đổi schema, `makemigrations --check` không có thay đổi.
- 30/10/2026, SonarCloud `test_publisher.py:93`, `:106` (khối `pytest.raises` có hai lời gọi có thể ném): dựng `SampleHappenedV1` và `handles(...)` trước khối, trong khối chỉ còn `publish(event)` và `register(...)`; hành vi test không đổi, 212 test xanh.

#### Review

Ba trục: Spec, Standards, Bug (`/code-review high`). Vòng sửa R1 (`45420e6`), 212 test xanh.

| Mã | Chỗ | Kết luận | Lý do |
| --- | --- | --- | --- |
| B1 | `modules/apps.py` | đã sửa | `ModulesConfig.ready()` gọi `shared.events.registry.autodiscover("modules")` nạp `events.py`/`handlers.py` (02 §5); thiếu thì relay/worker không có handler |
| B2 | `shared/management/commands/run_outbox_relay.py` | đã sửa | Mỗi bước try riêng; lỗi `create_deliveries` không chặn `dispatch_due` |
| B5, S11, T4, T3, T7 | `shared/events/relay.py` | đã sửa | Chỉ bắt `kombu` `OperationalError`, dừng lô ở lỗi đầu, log `WARNING` `outbox_dispatch_failed` kèm `deferred`; lỗi khác ném ra (07 §1.3); bỏ `queue=` lặp |
| B4 | `shared/events/publisher.py` | đã sửa | `publish()` ngoài `atomic` ném `RuntimeError` |
| B10 | `shared/events/registry.py` | đã sửa | Tên handler quá `HANDLER_NAME_MAX_LENGTH = 100` ném `ImproperlyConfigured` lúc import |
| B8 | `shared/events/consumer.py` | đã sửa | `completed_at`, `failed_at`, lịch retry lấy thời điểm sau khi handler chạy |
| S1 | `test_relay.py` | đã sửa | Test `transaction=True`: hạn giao lại đã commit khi gọi broker; relay chết trước enqueue thì giao lại sau hạn |
| S2 | `test_consumer.py` | đã sửa | `pg_terminate_backend` trong handler: `DatabaseError` ném ra, delivery giữ `pending`, `attempts = 0` |
| S3, S4 | `test_relay.py` | đã sửa | Hai `dispatch_due` đồng thời không giao trùng; mất task với `attempts = 2` không reset bộ đếm |
| S7, S8, T10 | `test_relay.py`, `test_drain.py`, `test_consumer.py` | đã sửa | Kiểm DB thay vì chỉ mock; vòng lặp chạy tiếp sau lỗi; đổi tên biến |
| B3 | `shared/events/consumer.py` | chỉ báo | Handler bị kill do time limit được giao lại vô hạn; 07 cố ý không tính task mất là lượt retry → ticket [24](./24-outbox-killed-handler-redispatch.md) |
| B6 | `shared/events/relay.py` | chỉ báo | Thông lượng 100/giây → ticket [25](./25-outbox-relay-throughput.md) |
| B7 | `shared/events/consumer.py` | chỉ báo | Payload không hợp lệ retry 5 lần theo bảng 07 §1.3 → ticket [27](./27-outbox-invalid-payload-fails-fast.md) |
| T5, T6, T8, T9, T11 | nhiều file | chỉ báo | Smell (chuyển trạng thái trên model, `due()`, mixin UUID, helper test, mặc định factory) → ticket [26](./26-outbox-refactor-smells.md) |
| B9 | `shared/testing/events.py` | chỉ báo | `drain_events` dùng `connection.run_on_commit` (API riêng của Django); không có API công khai chạy callback đang chờ |
| T2 | `test_relay.py` | chỉ báo | Patch hàm nội bộ để giả lỗi DB; lỗi DB thật khó tạo ổn định cho test vòng lặp |
| S5, S6, S12 | — | chỉ báo | Chưa test SIGTERM; marker `concurrency` (ticket 02); hai handler giao lặp đồng thời (đã có từng phần) |
| T1 | 02 §5, 08 | chỉ báo | Tài liệu cập nhật ở phase sync |
| S9, S10, T12 | — | bác | Triage 22/23 là bước của skill; factory do phiên chính giao; `isolated()` đã chốt trong Quyết định |

#### Commit

| Task | Phase | AC | Commit | File |
| --- | --- | --- | --- | --- |
| plan | 1 grill | — | `572f6df` docs: plan shared events outbox ticket | 3 |
| S1 | 2 code | 7 | `8b437e4` feat(shared): add outbox models, DomainEvent, publish and handler registry | 11 |
| S2 | 2 code | 3, 4, 7 | `fcd91a4` feat(shared): add event consumer, dispatch_event task and celery ack settings | 5 |
| S3 | 2 code | 2, 5, 6, 7 | `d98563e` feat(shared): add outbox relay, run_outbox_relay command and relay service | 10 |
| S4 | 2 code | 1 | `0888ebc` feat(shared): add enqueue_on_commit and drain_events test helper | 4 |
| R1 | 4 review | — | `d6cf2ab` fix(shared): address review findings on outbox relay and consumer | 12 |
| sync | 5 sync | — | `8b28aa7` docs: sync docs and report for shared events outbox ticket | 8 |

#### Tài liệu đã cập nhật

- `docs/architecture/02-backend-structure.md` §5: `shared/events/__init__.py` (thêm `DomainEvent`), `publisher.py` (ném `RuntimeError` ngoài transaction), `registry.py` (`@handles(..., name=)`, `autodiscover`), migration `0003_outbox`, factory outbox, `modules/apps.py` (nạp `events.py`, `handlers.py`); §6.1 ví dụ `handlers.py` có `name=`.
- `docs/architecture/08-local-development.md`: bảng lệnh `make restart-worker` (khởi động lại cả relay), bỏ ghi chú "từ ticket 10" ở Compose rút gọn.
- `.scratch/mvp-roadmap/map.md`: Decisions-so-far về API sự kiện của `shared` và ticket mới 24–27.
- Ticket mới `needs-triage`: [24](./24-outbox-killed-handler-redispatch.md), [25](./25-outbox-relay-throughput.md), [26](./26-outbox-refactor-smells.md), [27](./27-outbox-invalid-payload-fails-fast.md).
