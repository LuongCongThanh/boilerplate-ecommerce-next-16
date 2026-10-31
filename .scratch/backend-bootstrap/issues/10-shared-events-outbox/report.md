# Báo cáo

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
- `delivery_lag`, `get_delivery_outcomes`, purge, `retry_failed_events`, `replay_events`: thuộc ticket [18](../18-outbox-operations/spec.md).
- Sentry Cron check-in của relay (07 §3.4): chờ cấu hình Sentry.

#### Gap

- Test giao trùng đồng thời và hai relay đồng thời chưa gắn marker `concurrency` (12 §2.2); ticket [02](../02-pytest-markers-and-br-report/spec.md) khai báo marker rồi gắn.
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
| B3 | `shared/events/consumer.py` | chỉ báo | Handler bị kill do time limit được giao lại vô hạn; 07 cố ý không tính task mất là lượt retry → ticket [24](../24-outbox-killed-handler-redispatch/spec.md) |
| B6 | `shared/events/relay.py` | chỉ báo | Thông lượng 100/giây → ticket [25](../25-outbox-relay-throughput/spec.md) |
| B7 | `shared/events/consumer.py` | chỉ báo | Payload không hợp lệ retry 5 lần theo bảng 07 §1.3 → ticket [27](../27-outbox-invalid-payload-fails-fast/spec.md) |
| T5, T6, T8, T9, T11 | nhiều file | chỉ báo | Smell (chuyển trạng thái trên model, `due()`, mixin UUID, helper test, mặc định factory) → ticket [26](../26-outbox-refactor-smells/spec.md) |
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
- Ticket mới `needs-triage`: [24](../24-outbox-killed-handler-redispatch/spec.md), [25](../25-outbox-relay-throughput/spec.md), [26](../26-outbox-refactor-smells/spec.md), [27](../27-outbox-invalid-payload-fails-fast/spec.md).
