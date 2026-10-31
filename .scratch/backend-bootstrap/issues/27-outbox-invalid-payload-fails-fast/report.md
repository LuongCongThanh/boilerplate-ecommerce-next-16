# Báo cáo

### Báo cáo 01/11/2026

**Nhánh:** `fix/outbox-invalid-payload-fails-fast` · **PR:** chưa mở · **Mode:** lite

#### Đã làm

| AC | Bằng chứng |
| --- | --- |
| 1. Payload không parse được bằng class sự kiện thì delivery `failed` ngay lần đầu, có `failed_at`, `last_error`, log `ERROR` | `shared/events/tests/test_consumer.py::test_invalid_payload_fails_without_calling_handler`, `::test_invalid_payload_fails_before_interrupted_runs_check`, `::test_non_validation_parse_error_fails_with_traceback` (2 case: `validator_raises`, `payload_not_dict`) |
| 2. Lỗi trong handler (sau khi parse thành công) vẫn theo lịch retry cũ | `shared/events/tests/test_consumer.py::test_validation_error_inside_handler_schedules_retry`; các test retry có sẵn (`test_exception_rolls_back_handler_and_schedules_retry`, `test_exhausted_retries_mark_failed`) vẫn xanh |

`make lint` xanh (ruff, mypy, import-linter: 1 contract kept) · `make test`: 320 passed trong 9.93s

#### Chưa làm

- Không

#### Gap

- Test AC2 và `test_invalid_payload_fails_before_interrupted_runs_check` xanh ngay từ lần chạy đầu, vì code đã đúng thứ tự. Hai test này giữ vai trò chặn hồi quy.
- AC1 được hiểu rộng hơn chữ trong ticket: mọi lỗi lúc parse đều `failed` ngay, không chỉ `ValidationError` (người dùng duyệt ở review, B1).
- Thay đổi phá vỡ class `…V1` vẫn chỉ bị bắt sau khi deploy. Contract test snapshot schema sự kiện đã ghi vào backlog, mốc M1.

#### Thay đổi theo yêu cầu

- Không

#### Review

| Mã | Chỗ | Kết luận | Lý do |
| --- | --- | --- | --- |
| B1 | `shared/events/consumer.py:82` | đã sửa | Lỗi parse khác `ValidationError` thoát khỏi transaction 1, relay giao lại vô hạn; nay `failed` ngay, log kèm traceback |
| B5 / St5 | `shared/events/consumer.py:151,160` | đã sửa | Ba nhánh `failed` ngay dùng chung `_fail_now` |
| B7 | `shared/events/consumer.py:168` | đã sửa | `invalid_fields` chỉ ghi field gốc + type, bỏ trùng: không lọt key từ dữ liệu, kích thước có giới hạn |
| B4 / Sp1 | `shared/events/tests/test_consumer.py:157` | đã sửa | Thêm test thứ tự parse trước `interrupted_runs`, bộ đếm khác 0 giữ nguyên |
| Sp2 | `shared/events/tests/test_consumer.py:178` | đã sửa | Khẳng định đúng một log ERROR |
| B2 | `docs/architecture/07-async-events-jobs.md:65` | đã sửa | Bỏ hướng dẫn sai "thêm version rồi mở lại" |
| B3 / St1 / Sp3 / St4 | `consumer.py:3`, `07` §1.1.1, sơ đồ, §5 | đã sửa | Mô tả transaction 1 và kịch bản test có thêm bước parse |
| St2 | `docs/architecture/03-data-model.md:194,207` | đã sửa | `failed_at` có thêm nguyên nhân thứ ba |
| St3 | `shared/events/tests/test_consumer.py:189` | chỉ báo | Kiểm PII bằng `capture_logs` thay vì `json_logging` (12 §4); repo có tiền lệ, cách này bỏ qua `redact_pii` nên chặt hơn; ghi ở PR |
| St6 | `shared/events/tests/test_consumer.py` | chỉ báo | Đoạn lọc log `event_delivery_failed` lặp ở vài test (smell) |
| B6 | — | chỉ báo → backlog | Contract test schema sự kiện trong CI, mốc M1 |

#### Commit

| Task | Phase | AC | Commit | File |
| --- | --- | --- | --- | --- |
| plan | 1 grill | — | `238d13a` docs: plan outbox invalid payload fails fast ticket | 2 |
| S1 | 2 code | 1, 2 | `f3ce9a9` fix(shared): fail deliveries whose payload no longer fits the event class | 3 |
| R1 | 4 review | — | `6a2ed80` fix(shared): address review findings on invalid outbox payload | 4 |

#### Tài liệu đã cập nhật

- `docs/architecture/07-async-events-jobs.md`:
  - §1.3: thêm dòng "payload không parse được" vào bảng kết quả của consumer, ghi rõ chuyển `failed` ngay, nội dung `invalid_fields`, cách mở lại đúng, và việc lỗi trong handler vẫn được retry.
  - §1.1.1 và sơ đồ: thêm bước parse ở transaction 1.
  - §5: thêm kịch bản test.
- `docs/architecture/03-data-model.md`: cột `failed_at` và ghi chú có thêm nguyên nhân "payload không parse được".
