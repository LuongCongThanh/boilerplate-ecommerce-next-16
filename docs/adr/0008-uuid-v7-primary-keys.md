# Khoá chính UUID v7, sinh bằng `uuid-utils`

Mọi bảng dùng khoá chính UUID v7, sinh trong `shared.models.BaseModel` bằng `uuid_utils.compat.uuid7` (bản `compat` trả `uuid.UUID` chuẩn mà `UUIDField` của Django nhận được). UUID không lộ số lượng đơn hay khách qua ID tăng dần; v7 có tiền tố thời gian nên sắp xếp được theo thời gian tạo và không làm index B-tree phân mảnh như v4. Python 3.13 chưa có `uuid.uuid7()` (có từ 3.14) nên tạm dùng package ngoài.

## Các phương án đã cân nhắc

- **Số tự tăng (`BigAutoField`)**: loại, vì lộ quy mô kinh doanh qua ID trong URL và API.
- **UUID v4 (`uuid.uuid4`, có sẵn)**: loại, vì ngẫu nhiên hoàn toàn nên chèn rải rác khắp index và không sắp xếp được theo thời gian.

## Hệ quả

- Khi nâng lên Python 3.14, đổi `default` sang `uuid.uuid7` và bỏ `uuid-utils`. Giá trị đã lưu không cần migrate.
