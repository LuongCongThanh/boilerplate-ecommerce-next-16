# PostgreSQL, Redis và Celery làm runtime của backend

Django API lưu dữ liệu trong PostgreSQL, dùng Redis làm cache và broker, và chạy các việc theo thời gian hoặc chậm trong Celery worker cùng Celery Beat: hết hạn Giữ hàng sau 15 phút, gửi thông báo, đối soát trạng thái thanh toán và GHN. Chọn PostgreSQL vì tính toàn vẹn giao dịch khi trừ Tồn kho (`SELECT ... FOR UPDATE`), và chọn Celery vì đây là stack task phổ biến nhất trong cộng đồng Django, dễ tuyển người.

## Hệ quả

- Việc hết hạn Giữ hàng phụ thuộc vào Celery Beat đang chạy, nên code checkout vẫn phải coi một Giữ hàng đã quá hạn là không hợp lệ ngay khi đọc, không chỉ trông vào job.
