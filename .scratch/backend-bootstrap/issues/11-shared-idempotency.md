# Xử lý header `Idempotency-Key`

Status: ready-for-agent

Blocked by: 16

Spec: [spec.md](../spec.md)

## Việc cần làm

- Model `IdempotencyKey` theo [03 mục 1.5](../../../docs/architecture/03-data-model.md#15-shared_idempotency_key-khoá-chống-tạo-trùng).
- `shared/api/idempotency.py`: claim key bằng transaction ngắn kèm lease, lưu kết quả cùng transaction với tác động nghiệp vụ, replay kết quả đã `completed`, theo quy ước ở [04 mục 1](../../../docs/architecture/04-api-contract.md#1-quy-ước-chung). Scope = method + endpoint chuẩn hoá + danh tính (Tài khoản hoặc guest cart token).
- Job `purge_idempotency_keys`: chỉ xoá bản ghi `completed` quá 24 giờ.
- Một endpoint mẫu chỉ có trong `config.settings.test` để test hành vi.

## Quyết định

Chốt khi grilling ngày 30/10/2026.

| Chủ đề | Quyết định |
|---|---|
| Tài liệu chi phối | `shared/models.py`, `shared/migrations/0004_idempotency_key.py`: 03 §1.5, 03 §0.1 (BaseModel), 02 §9.1 (khoá chính), §9.2 (tên bảng, tên constraint), ADR 0008. `shared/api/idempotency.py`: 04 §1 (*Chống tạo trùng*), 04 §3 (ErrorDTO, 409), 04 §5.2 (`IdempotencyPendingDTO`), 03 §1.5 (ghi chú claim/lease), 02 §5 (cây `shared/api/`), 02 §9.1 (*Transaction*), §9.6 (logging). `shared/tasks.py`, `config/celery.py`: 07 §3.2 (`shared.purge_idempotency_keys` 03:45), 02 §9.2 (tên Celery task). `shared/testing/factories.py`: 02 §9.5. Test: 12 §2.2 (concurrency), 12 §2.4 (Idempotency-Key), 02 §9.2 (tên file test), §9.5 (factory, time-machine) |
| Model | `IdempotencyKey(BaseModel)` trong `shared/models.py` (02 §5), `db_table = "shared_idempotency_key"`. Cột, `UNIQUE(scope, key)`, hai `CHECK` và partial index `completed_at WHERE status='completed'` đúng 03 §1.5. Kế thừa `BaseModel` (có `id`, `created_at`, `updated_at`) theo 03 §0.1, khác outbox vì 03 §1.5 không loại trừ. `status` là `TextChoices` `in_progress/completed`; `operation_id` UK `default=uuid7` sinh khi claim |
| API | Hàm hai bước trong `shared/api/idempotency.py`, không dùng decorator bọc view (checkout gọi GHN ngoài transaction, kết quả phải lưu trong transaction của service). `begin(request)` chạy transaction ngắn, trả một trong: `Replay` (status/body đã lưu), `Pending` (có `retry_after`, `response()` dựng `202 IdempotencyPendingDTO` + `Retry-After: 3`; người gọi tự dựng body 202 khác được, như `PaymentStartDTO`), `Claim` (`operation_id`, `lease_token`). Khác `request_hash` → raise `IdempotencyConflict` (`DomainError`, `409 IDEMPOTENCY_CONFLICT`), kể cả khi key còn `in_progress`. Service gọi `claim.complete(status, body, resource_id=None)` **bên trong** `atomic` của mình: khoá dòng key, lease không còn khớp thì raise để transaction nghiệp vụ rollback. Kiểm quyền/sở hữu là việc của view, làm trước `begin` |
| Lỗi nghiệp vụ / rollback | `Claim` là context manager: exception thoát ra thì mở transaction ngắn, xoá dòng key nếu lease vẫn của mình và `resource_id` còn NULL, để gửi lại cùng key chạy lại từ đầu (AC4). Có `resource_id` thì giữ dòng cho luồng khôi phục. Không lưu response lỗi thành `completed` (04 §1: body đổi/quote mới dùng key mới) |
| Lease | Hằng `LEASE = 60 giây` trong module. `in_progress` còn lease → `Pending`; lease đã hết và cùng hash → giành lại với `lease_token` mới; worker cũ gọi `complete` thấy lệch lease thì raise, tác động của nó rollback theo |
| Scope | `"{METHOD} {path}\|{identity}"`: `path` là `request.path` (đã gồm ID/mã tài nguyên), bỏ `/` cuối. `identity` = `account:<pk>` khi `request.user.is_authenticated` (cùng cách `AccountThrottle`), ngược lại `cart:<sha256(X-Cart-Token)>`; không lưu token thô. Không có danh tính → `400 VALIDATION_ERROR` |
| `request_hash` | SHA-256 của `request.data` đã parse, chuẩn hoá bằng `json.dumps(sort_keys=True, separators=(",", ":"), ensure_ascii=False)`; tính trước serializer |
| Thiếu / sai header | Thiếu `Idempotency-Key` hoặc không phải UUID → `400 VALIDATION_ERROR`, `details` trỏ `Idempotency-Key` (04 §1 bắt buộc key; 12 §2.4 đòi test thiếu key). Không có trong AC, thêm theo tài liệu |
| Endpoint mẫu | View trong `shared/tests/api_urls.py`, chỉ nạp qua `pytest.mark.urls` (tiền lệ ticket 16): đây là cách hiểu "chỉ có trong `config.settings.test`", không đụng `config/urls.py`. Tác động nghiệp vụ là một dòng ở bảng chỉ dùng cho test tạo bằng `schema_editor` (mẫu `HandlerEffect`, `shared/tests/test_models.py`); cờ trong body làm view raise sau khi ghi, cho AC4 |
| Purge | `purge_idempotency_keys() -> int` trong `shared/api/idempotency.py`; xoá theo lô `PURGE_BATCH = 1000` (`select_for_update().order_by("id")`) như `purge_old_outbox_events`; điều kiện `status=completed AND completed_at < now - 24h` (đúng mốc 24 giờ chưa xoá); log `idempotency_keys_purged` kèm `count`. Celery task `shared.purge_idempotency_keys` (queue `default`) trong `shared/tasks.py` chỉ gọi hàm này; `config/celery.py` lịch `crontab(hour=3, minute=45)` |
| Concurrency | Hai request đồng thời cùng key: test `django_db(transaction=True)` + thread + `threading.Barrier` (12 §2.2, §2.4): đúng một lần tác động, một `operation_id`, bên kia nhận 202 |
| Ngoài phạm vi | `claim.attach_resource()` (ghi `resource_id` và commit trước khi gọi gateway) và `202 PaymentStartDTO`: ticket Thanh toán M2 thêm. Gắn `Idempotency-Key` vào checkout, Thanh toán, kho: ticket của các module đó |

## Kế hoạch

Sinh bằng `plan.py` từ state của skill. Mỗi task là đúng một commit có trailer `Task: <task>`.

| Task | AC | Seam | Test dự kiến | File | Sau |
| --- | --- | --- | --- | --- | --- |
| S1 | 1, 2, 5 | idempotency.begin(request) / claim.complete() qua endpoint mẫu POST trong shared.tests.api_urls (APIClient) | `shared/tests/test_api_idempotency.py::test_same_key_same_body_replays_saved_response_without_rerun`<br>`shared/tests/test_api_idempotency.py::test_body_key_order_does_not_change_request_hash`<br>`shared/tests/test_api_idempotency.py::test_same_key_different_body_returns_idempotency_conflict`<br>`shared/tests/test_api_idempotency.py::test_same_key_different_account_does_not_see_other_result`<br>`shared/tests/test_api_idempotency.py::test_same_key_different_cart_token_does_not_see_other_result`<br>`shared/tests/test_api_idempotency.py::test_request_without_identity_returns_validation_error`<br>`shared/tests/test_api_idempotency.py::test_missing_key_returns_validation_error`<br>`shared/tests/test_api_idempotency.py::test_non_uuid_key_returns_validation_error` | `backend/shared/models.py`<br>`backend/shared/migrations/0004_idempotency_key.py`<br>`backend/shared/api/idempotency.py`<br>`backend/shared/testing/factories.py`<br>`backend/shared/tests/api_urls.py`<br>`backend/shared/tests/test_api_idempotency.py` | — |
| S2 | 3, 4 | lease + Claim context manager qua endpoint mẫu; IdempotencyKeyFactory dựng key in_progress | `shared/tests/test_api_idempotency.py::test_in_progress_key_returns_pending_with_retry_after`<br>`shared/tests/test_api_idempotency.py::test_different_body_conflicts_even_while_in_progress`<br>`shared/tests/test_api_idempotency.py::test_expired_lease_is_taken_over`<br>`shared/tests/test_api_idempotency.py::test_business_rollback_leaves_key_not_completed`<br>`shared/tests/test_api_idempotency.py::test_stale_lease_complete_rolls_back_effect`<br>`shared/tests/test_api_idempotency.py::test_concurrent_same_key_runs_effect_once` | `backend/shared/api/idempotency.py`<br>`backend/shared/tests/api_urls.py`<br>`backend/shared/tests/test_api_idempotency.py` | S1 |
| S3 | 6 | purge_idempotency_keys() và task shared.purge_idempotency_keys trong beat_schedule | `shared/tests/test_idempotency_purge.py::test_purge_keeps_in_progress_keys`<br>`shared/tests/test_idempotency_purge.py::test_purge_deletes_completed_older_than_24h`<br>`shared/tests/test_idempotency_purge.py::test_purge_keeps_completed_at_exact_24h`<br>`shared/tests/test_idempotency_purge.py::test_purge_runs_in_batches`<br>`shared/tests/test_idempotency_purge.py::test_purge_scheduled_daily_0345` | `backend/shared/api/idempotency.py`<br>`backend/shared/tasks.py`<br>`backend/config/celery.py`<br>`backend/shared/tests/test_idempotency_purge.py` | S1 |

Commit dự kiến: `plan` → `S1` → `S2` → `S3` → `R1 (khi review cần sửa)` → `sync` → `close`.

## Acceptance criteria

- [ ] Cùng key, cùng body: lần hai trả nguyên status và body đã lưu, không chạy lại tác động.
- [ ] Cùng key, khác body: `409 IDEMPOTENCY_CONFLICT`.
- [ ] Cùng key khi lần đầu còn xử lý: `202 IdempotencyPendingDTO` kèm `Retry-After`.
- [ ] Tác động nghiệp vụ rollback thì key không ở trạng thái `completed`.
- [ ] Cùng key nhưng khác danh tính không thấy kết quả của nhau.
- [ ] Purge không xoá key `in_progress`.
