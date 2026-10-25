# Sự kiện giữa các module: Outbox + Celery trên Redis, chưa dùng Kafka

Sự kiện giữa các module (`OrderPlaced`, `PaymentSucceeded`…) được ghi vào bảng `outbox` trong cùng transaction với dữ liệu nghiệp vụ. Một relay đọc bảng này và đẩy từng sự kiện thành Celery task trên Redis đã có sẵn. Phía nhận là các handler idempotent, dùng bảng `processed_events` để bỏ qua sự kiện đã xử lý. Mọi việc gửi và nhận đều đi qua interface `EventPublisher`/`EventConsumer` trong `shared/events/`.

Lý do chưa dùng Kafka: ở tải MVP (khoảng 10k–200k sự kiện/ngày), MSK tại Singapore tốn khoảng 87–730 USD/tháng và cần người vận hành, trong khi Celery trên Redis không phát sinh thêm chi phí và chạy giống hệt nhau ở local và trên AWS.

## Các phương án đã cân nhắc

- **Kafka ở cả local và AWS (MSK)**: chưa chọn vì chi phí và công vận hành không tương xứng với quy mô hiện tại.
- **Kafka ở local, SNS+SQS trên AWS**: không chọn, vì local và production chạy hai công nghệ khác nhau, dễ sinh lỗi chỉ có trên production.

## Hệ quả

- Không có đảm bảo thứ tự sự kiện. Mỗi handler phải kiểm tra trạng thái hiện tại, và máy trạng thái của Đơn hàng phải từ chối những chuyển trạng thái không hợp lệ.
- Không replay được sự kiện qua broker. Nếu cần, bảng `outbox` đóng vai event log.
- Chỉ `shared/events/` được import thư viện broker. `import-linter` kiểm tra quy tắc này.

## Hướng mở rộng

- **Chuyển sang Kafka** khi có một trong các điều kiện: lưu lượng vượt khoảng 1.000 sự kiện/giây liên tục, cần phát lại lịch sử cho hệ thống mới (analytics, search, CDC), cần stream processing, hoặc có người vận hành Kafka. Khi đó chỉ cần viết thêm một adapter `EventPublisher` cho Kafka, với tên topic theo dạng `<module>.<event>.v<version>` và client `confluent-kafka`.
- **Schema Registry** chỉ cần khi dùng Kafka và có nhiều service hoặc team độc lập. Vì sự kiện đã là class Pydantic có version, việc bổ sung ước tính khoảng 3–5 ngày công nếu dùng JSON Schema.
