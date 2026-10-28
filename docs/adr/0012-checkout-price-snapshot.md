# Chốt giá dưới khoá Biến thể trong transaction checkout

Checkout báo giá và gọi GHN ngoài transaction để tránh giữ khoá khi chờ mạng. Trước khi tạo Đơn hàng, khoá toàn bộ StockItem, rồi toàn bộ Variant theo thứ tự ổn định và kiểm tra lại checkout_version, Giá áp dụng, snapshot và điều kiện bán. Mọi writer của catalog, kể cả tạo/sửa/xoá SalePrice, phải khoá Variant bị ảnh hưởng trước khi ghi. Chỉ khoá Variant ở checkout mà không ràng buộc writer không bảo vệ được việc thêm Giá khuyến mãi đồng thời.

Chọn từ chối bằng PRICE_CHANGED và yêu cầu xác nhận quote mới khi dữ liệu thay đổi, thay vì cho phép dùng báo giá cũ. Đánh đổi là checkout phải khoá Variant ngay cả khi availability không đổi, và có thể yêu cầu xác nhận lại dù tổng tiền không đổi. Nếu cần quote mới, rollback trước rồi mới gọi tích hợp bên ngoài; OrderLine giữ snapshot sau commit.
