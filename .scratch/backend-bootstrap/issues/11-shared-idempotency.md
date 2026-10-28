# Xử lý header `Idempotency-Key`

Status: ready-for-agent

Blocked by: 09

Spec: [spec.md](../spec.md)

## Việc cần làm

- Model `IdempotencyKey` theo [03 mục 1.5](../../../docs/architecture/03-data-model.md#15-shared_idempotency_key-khoá-chống-tạo-trùng).
- `shared/api/idempotency.py`: claim key bằng transaction ngắn kèm lease, lưu kết quả cùng transaction với tác động nghiệp vụ, replay kết quả đã `completed`, theo quy ước ở [04 mục 1](../../../docs/architecture/04-api-contract.md#1-quy-ước-chung). Scope = method + endpoint chuẩn hoá + danh tính (Tài khoản hoặc guest cart token).
- Job `purge_idempotency_keys`: chỉ xoá bản ghi `completed` quá 24 giờ.
- Một endpoint mẫu chỉ có trong `config.settings.test` để test hành vi.

## Acceptance criteria

- [ ] Cùng key, cùng body: lần hai trả nguyên status và body đã lưu, không chạy lại tác động.
- [ ] Cùng key, khác body: `409 IDEMPOTENCY_CONFLICT`.
- [ ] Cùng key khi lần đầu còn xử lý: `202 IdempotencyPendingDTO` kèm `Retry-After`.
- [ ] Tác động nghiệp vụ rollback thì key không ở trạng thái `completed`.
- [ ] Cùng key nhưng khác danh tính không thấy kết quả của nhau.
- [ ] Purge không xoá key `in_progress`.
