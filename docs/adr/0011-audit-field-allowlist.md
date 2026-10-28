# Audit theo danh sách field, không sao chép raw payload chứa PII

Fashion Store cần lịch sử trạng thái, tiền và Tồn kho để vận hành, đồng thời cần ẩn danh thông tin liên hệ mà không để lại bản sao trong bảng history. Chọn cấu hình `django-pghistory` theo danh sách field tường minh trong [mô hình dữ liệu mục 10.1](../architecture/03-data-model.md#101-các-field-được-ghi-lịch-sử), thay vì ghi toàn bộ model hoặc toàn bộ nhóm bảng `payments_*`.

Không tạo history cho payload nhà cung cấp, thông tin liên hệ, token và nội dung email. Đánh đổi là không tái dựng được toàn bộ payload cũ từ history; dữ liệu tích hợp hiện hành có quy trình redaction riêng. ID liên kết trong history vẫn cần kiểm soát truy cập. Mọi field audit mới phải review phạm vi PII và khả năng ẩn danh; nếu đã có history chứa PII thì phải làm sạch dữ liệu cũ, không chỉ sửa tracker.

Cấu hình tracker dùng `fields` để liệt kê field, đồng thời kiểm soát context của history: [tài liệu django-pghistory](https://django-pghistory.readthedocs.io/en/3.2.0/event_tracking/).
