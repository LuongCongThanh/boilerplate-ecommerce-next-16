# Adapter cho nhà cung cấp bên ngoài, cổng giả lập và job đối soát

VNPay, MoMo và GHN được gọi qua interface chung (`PaymentGateway`, `ShippingProvider`), mỗi nhà cung cấp là một adapter, chọn adapter nào qua cấu hình. Lý do: server của nhà cung cấp không gọi được IPN hay webhook vào máy local, mà ta muốn phát triển và test hoàn toàn offline. Vì vậy:

- **Cổng giả lập (Fake Gateway)** là mặc định ở local và khi test. Đây là một trang giả lập chạy ngay trong Django, cho bấm "Thành công" hoặc "Thất bại" rồi tự gọi IPN nội bộ.
- **Job đối soát** chạy ở mọi môi trường: định kỳ gọi API query của nhà cung cấp để cập nhật các thanh toán và vận đơn còn treo. Job này là lưới an toàn khi lỡ mất IPN hoặc webhook.

Return URL (trình duyệt quay về) không bao giờ được dùng để xác nhận thanh toán.

## Các phương án đã cân nhắc

- **Tunnel (Cloudflare Tunnel / ngrok)** để sandbox thật gọi được vào máy local: không dùng hằng ngày vì phụ thuộc mạng và phải cấu hình lại URL, nhưng **sẽ dùng để nghiệm thu tích hợp thật trước khi lên AWS**.
- **Chỉ dùng Return URL**: loại, vì khách có thể đóng tab hoặc sửa tham số.

## Hệ quả

- Fake Gateway không kiểm tra được chữ ký thật của nhà cung cấp, nên việc kiểm tra chữ ký phải có unit test riêng với dữ liệu mẫu từ tài liệu của VNPay và MoMo.
- Khởi tạo Thanh toán phải lưu thao tác trước khi gọi gateway và khôi phục cùng mã khi chưa rõ kết quả ([ADR 0013](./0013-recoverable-payment-initiation.md)). Fake Gateway cần mô phỏng cả trường hợp đã tạo giao dịch nhưng client bị timeout, và truy vấn lại theo mã cũ; không chỉ mô phỏng thành công/thất bại.
- GHN tạo Vận đơn cũng có trạng thái chưa rõ kết quả: giữ cùng mã shop/snapshot, tra theo client_order_code trước khi retry. Timeout không phải failed; chỉ tự retry create khi cơ chế chống trùng đã được nghiệm thu. Cache báo giá hash toàn bộ request thực gửi, không chỉ địa chỉ và nhóm cân nặng (06 mục 4).
