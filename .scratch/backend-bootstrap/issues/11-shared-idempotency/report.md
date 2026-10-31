# Báo cáo

### Báo cáo 30/10/2026

**Nhánh:** `feat/shared-idempotency` · **PR:** #40 · **Mode:** full

#### Đã làm

| AC | Bằng chứng |
| --- | --- |
| 1. Cùng key, cùng body: trả lại status/body đã lưu, không chạy lại tác động | `shared/tests/test_api_idempotency.py::test_same_key_same_body_replays_saved_response_without_rerun`, `::test_body_key_order_does_not_change_request_hash`, `::test_lone_surrogate_in_body_is_hashed` |
| 2. Cùng key, khác body: `409 IDEMPOTENCY_CONFLICT` | `shared/tests/test_api_idempotency.py::test_same_key_different_body_returns_idempotency_conflict`, `::test_different_body_conflicts_even_while_in_progress` |
| 3. Lần đầu còn xử lý: `202 IdempotencyPendingDTO` + `Retry-After` | `shared/tests/test_api_idempotency.py::test_in_progress_key_returns_pending_with_retry_after`, `::test_expired_lease_is_taken_over`, `::test_concurrent_same_key_runs_effect_once` |
| 4. Tác động rollback thì key không `completed` | `shared/tests/test_api_idempotency.py::test_business_rollback_leaves_key_not_completed`, `::test_error_after_complete_leaves_key_not_completed`, `::test_stale_lease_complete_rolls_back_effect`, `::test_complete_after_key_deleted_raises_lease_lost`, `::test_rollback_keeps_key_with_resource_id`, `::test_complete_without_resource_id_keeps_attached_resource_id`, `::test_claim_inside_outer_transaction_raises` |
| 5. Khác danh tính không thấy kết quả của nhau | `shared/tests/test_api_idempotency.py::test_same_key_different_account_does_not_see_other_result`, `::test_same_key_different_cart_token_does_not_see_other_result`, `::test_same_key_different_path_or_method_does_not_see_other_result`, `::test_account_scope_is_method_path_and_account_pk`, `::test_request_without_identity_returns_validation_error` |
| 6. Purge không xoá key `in_progress` | `shared/tests/test_idempotency_purge.py::test_purge_keeps_in_progress_keys`, `::test_purge_deletes_completed_older_than_24h`, `::test_purge_keeps_completed_at_exact_24h`, `::test_purge_runs_in_batches`, `::test_purge_scheduled_daily_0345` |

Thêm theo `## Quyết định` (04 §1, 12 §2.4): thiếu key hoặc key không phải UUID → `400 VALIDATION_ERROR` (`::test_missing_key_returns_validation_error`, `::test_non_uuid_key_returns_validation_error`); body không phải JSON → `415` (`::test_multipart_body_returns_unsupported_media_type`).

`make lint` xanh (ruff, mypy `--no-incremental`, import-linter 1 kept / 0 broken) · `make test`: 266 passed trong 9.65s

#### Chưa làm

- Không. `claim.attach_resource()` và `202 PaymentStartDTO` để ticket Thanh toán (M3) theo `## Quyết định`.

#### Gap

- Test concurrency chưa gắn `@pytest.mark.concurrency` (12 §2.2) vì marker chưa đăng ký; việc đăng ký thuộc ticket [02](../02-pytest-markers-and-br-report/spec.md).
- `shared/tests/test_models.py`: model test `Widget` khai báo lại `objects = BaseQuerySet.as_manager()` vì `IdempotencyKey` là lớp con cụ thể đầu tiên của `BaseModel`, làm mypy (django-stubs) suy sai kiểu manager. Model test sau này kế thừa `BaseModel` cũng cần dòng này.
- Lease 60 giây không gia hạn (B5); `claim` chờ khoá dòng thay vì trả 202 ngay khi worker kia đang commit (B6); scope có thể vượt `varchar(255)` khi path dài hơn ~175 ký tự (B7); key `in_progress` bị bỏ lại khi worker chết, `resource_id` NULL, không bao giờ bị purge (B8, 03 §1.5 và 07 §3.2 hiện chỉ cho xoá `completed`). Chưa có nơi gọi nào chạm tới; xem lại khi checkout (M2) và Thanh toán (M3) dùng.

#### Thay đổi theo yêu cầu

- 30/10/2026: M0 xong khi có ticket 11 + 12 rồi vào M1; 01–04, 14, 19–23 thành backlog làm xen kẽ, 24–28 và 13 để trước go-live. Ghi vào `.scratch/mvp-roadmap/map.md` ở commit `sync`.
- 30/10/2026: phát hiện ngoài phạm vi khi review ticket này không tạo ticket `needs-triage` mới; retro sửa quy tắc của skill sang một file backlog chung.
- 30/10/2026 (CI PR #40): gitleaks `generic-api-key` bắt nhầm hằng `KEY` (UUID mẫu) trong `test_api_idempotency.py` → `# gitleaks:allow` và `.gitleaksignore` cho fingerprint của commit S1. SonarCloud: `test_claim_inside_outer_transaction_raises` chỉ giữ lời gọi `claim` trong `pytest.raises`.

#### Review

Ba trục: Spec (S), Standards (T), Bug (B). Vòng sửa R1 (`d4dfcbb`).

| Mã | Chỗ | Kết luận | Lý do |
| --- | --- | --- | --- |
| T4, T1, T7, T6 | `shared/api/idempotency.py` | đã sửa | Tách lõi sang `shared/idempotency.py` (service import được, 02 §6.1); `api/` chỉ đọc header, scope, hash; factory dùng `request_hash()` công khai |
| S5, S6, B2, B3, B10 | `shared/api/idempotency.py:111-121` | đã sửa | `complete()` là một `UPDATE` theo lease, 0 dòng → `LeaseLost`; không xoá `resource_id` cũ |
| B1 | `shared/api/idempotency.py:213` | đã sửa | Body không phải JSON → 415; encode `surrogatepass` |
| B4 | `shared/api/idempotency.py:139` | đã sửa | `atomic(durable=True)`: gọi trong transaction ngoài → `RuntimeError` |
| S1, S2 | `shared/tests/test_api_idempotency.py` | đã sửa | Thêm test lỗi sau `complete()`, khác path/method, scope `account:<pk>` |
| T2 | `shared/api/idempotency.py:46` | chỉ báo | Người dùng chọn giữ `LeaseLost` → 500; ghi vào `## Quyết định` |
| S4 | `shared/models.py:76` | chỉ báo | CHECK `status_valid` theo tiền lệ outbox; ghi vào 03 §1.5 ở sync |
| S3 | `test_api_idempotency.py` | chỉ báo | Marker `concurrency` thuộc ticket 02 |
| B5, B6, B7, B8 | `shared/idempotency.py` | chỉ báo | Ghi ở *Gap* |
| T3, T5, T8, T9, B9 | nhiều chỗ | chỉ báo | Smell: tên file test purge, monkeypatch `Claim.complete`, cặp `(status, body)`, tên `LEASE`/`begin`, vòng purge và kiểm danh tính trùng code có sẵn |

#### Commit

| Task | Phase | AC | Commit | File |
| --- | --- | --- | --- | --- |
| plan | 1 grill | — | `fc076b1` docs: plan shared idempotency ticket | 1 |
| S1 | 2 code | 1, 2, 5 | `e27a7df` feat(shared): add idempotency key claim and replay for Idempotency-Key | 7 |
| S2 | 2 code | 3, 4 | `d822e8f` feat(shared): add lease takeover and release on error for Idempotency-Key | 3 |
| S3 | 2 code | 6 | `5429eec` feat(shared): add daily purge job for completed Idempotency-Key | 4 |
| R1 | 4 review | — | `d4dfcbb` fix(shared): address review findings on idempotency | 7 |
| sync | 5 sync | — | `42e04b6` docs: sync docs and report for shared idempotency ticket | 5 |
| close | 6 ship | — | `bb39932` docs: close shared idempotency ticket | 1 |
| ci | 6 ship | — | `8dcadc0` test(shared): mark sample Idempotency-Key UUID as non-secret for gitleaks | 2 |
| ci | 6 ship | — | `3ac9e40` test(shared): keep only the claim call inside pytest.raises | 1 |

#### Tài liệu đã cập nhật

- `docs/architecture/02-backend-structure.md`: §5 cây thư mục thêm `shared/idempotency.py` (lõi) và mô tả lại `shared/api/idempotency.py` (lớp HTTP); §9.1 *Transaction* thêm `shared/idempotency.py` vào danh sách được mở transaction.
- `docs/architecture/04-api-contract.md`: §1 *Chống tạo trùng* thêm 400 khi thiếu/sai key và 415 khi body không phải JSON; §3 thêm dòng `415 UNSUPPORTED_MEDIA_TYPE`.
- `.scratch/backend-bootstrap/spec.md`: phạm vi ghi `shared.idempotency` và `shared.api.idempotency`.
- `.scratch/mvp-roadmap/map.md`: *Tiến độ* M0 (11 xong, 12 còn lại, backlog và để sau); *Decisions-so-far* thêm điều kiện đóng M0 và vị trí lõi idempotency.
