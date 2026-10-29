# Lưu thao tác khởi tạo Thanh toán trước khi gọi gateway

Timeout khi tạo giao dịch không chứng minh nhà cung cấp chưa tạo giao dịch. Chọn ghi thao tác idempotency, Payment và các mã tham chiếu ổn định vào PostgreSQL trước khi gọi gateway ngoài transaction; request lặp và job khôi phục dùng cùng Payment, lease và payload. Không sinh mã mới chỉ vì timeout. Query cùng giao dịch trước; chỉ retry create với cùng ID khi hợp đồng idempotency của adapter đã được xác minh.

Đánh đổi là API có thể trả 202 PAYMENT_INITIALIZING thay vì luôn trả redirect_url ngay; client thử lại cùng key và unresolved key không bị purge sau 24 giờ. Kết quả tạo tới sau IPN không được hạ trạng thái tiền. Không hứa luôn lấy lại được link nếu provider không hỗ trợ; giữ trạng thái chưa rõ, đối soát/cảnh báo hoặc trả kết quả giao dịch cuối. Chi tiết ở [06 mục 3.1](../architecture/06-integrations.md#31-khởi-tạo-thanh-toán-có-thể-khôi-phục).
