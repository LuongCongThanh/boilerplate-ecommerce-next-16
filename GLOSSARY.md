# Cửa hàng thời trang B2C (Fashion Store)

Website bán lẻ thời trang của một doanh nghiệp duy nhất cho khách hàng tại Việt Nam. Thuật ngữ được ghi song ngữ Việt / Anh; tên tiếng Anh là tên dùng trong code và tài liệu kiến trúc.

## Danh mục hàng hoá (Catalog)

**Sản phẩm (Product)**:
Một mẫu hàng chung mà khách nhìn thấy trên trang danh sách, ví dụ "Áo thun Basic". Khách không mua trực tiếp Sản phẩm mà mua một Biến thể của nó.
_Avoid_: Item, mặt hàng, hàng hoá

**Biến thể (Variant)**:
Một tổ hợp cụ thể của size và màu thuộc một Sản phẩm. Mỗi Biến thể có mã SKU, giá bán và tồn kho riêng, và là đơn vị mà khách thực sự mua.
_Avoid_: Option, phân loại, model

**Mã SKU (SKU)**:
Mã định danh duy nhất của một Biến thể.
_Avoid_: Product code, mã hàng

## Tồn kho (Inventory)

**Kho (Warehouse)**:
Một địa điểm vật lý nơi hàng được lưu trữ và xuất đi giao. Ở giai đoạn MVP chỉ có một Kho.
_Avoid_: Chi nhánh, store, location

**Tồn kho (Stock)**:
Số lượng một Biến thể đang có trong một Kho và còn bán được.
_Avoid_: Inventory count, số lượng

**Giữ hàng (Stock Reservation)**:
Phần Tồn kho bị tạm khoá cho một đơn chưa thanh toán online, có thời hạn 15 phút. Hết hạn mà chưa thanh toán thì phần giữ này được trả lại Tồn kho.
_Avoid_: Hold, lock, tạm giữ

## Khuyến mãi (Pricing & Promotions)

**Giá khuyến mãi (Sale Price)**:
Giá giảm gắn trực tiếp vào một Biến thể trong một khoảng thời gian, áp dụng tự động mà khách không cần nhập mã.
_Avoid_: Discount price, giá sale, promotion

**Mã giảm giá (Voucher)**:
Mã mà khách nhập khi checkout để được giảm trên toàn đơn, theo % hoặc số tiền cố định, có điều kiện và giới hạn lượt dùng. Mỗi Đơn hàng dùng tối đa một Voucher, và Voucher được cộng dồn với Giá khuyến mãi.
_Avoid_: Coupon, promo code, promotion

## Đơn hàng (Ordering)

**Đơn hàng (Order)**:
Một lần mua hàng của Khách vãng lai hoặc Khách hàng, gồm một hay nhiều Biến thể, giao tới một địa chỉ và thanh toán bằng một phương thức. Đơn chỉ được huỷ nguyên đơn, không huỷ từng phần.
_Avoid_: Purchase, transaction, giao dịch

**Dòng đơn hàng (Order Line)**:
Một Biến thể kèm số lượng và đơn giá tại thời điểm đặt, nằm trong một Đơn hàng.
_Avoid_: Order item, cart item

**Hoàn tất (Completed)**:
Trạng thái cuối của Đơn hàng, đạt được 7 ngày sau khi Đã giao, khi không còn yêu cầu Đổi trả nào đang mở. Đây là mốc hết quyền yêu cầu Đổi trả và là lúc doanh thu của đơn được chốt.
_Avoid_: Closed, finished, done

**Hoàn hàng (Returned to Sender)**:
Trạng thái của Đơn hàng khi giao thất bại và hãng vận chuyển trả hàng về Kho.
_Avoid_: Return, đổi trả, failed delivery

**Đổi trả (Return)**:
Yêu cầu của khách gửi lại hàng đã nhận trong vòng 7 ngày kể từ khi Đã giao, với hàng còn tag và chưa qua sử dụng. Hàng có Giá khuyến mãi giảm trên 50% không được Đổi trả.
_Avoid_: Refund, hoàn hàng, RMA

**Hoàn tiền (Refund)**:
Việc trả lại tiền về đúng cổng thanh toán mà khách đã dùng, phát sinh khi huỷ một đơn đã thanh toán online hoặc khi Đổi trả được chấp nhận.
_Avoid_: Chargeback, reimbursement

## Người dùng (Actors)

**Khách vãng lai (Guest)**:
Người mua hàng mà không có tài khoản, được nhận diện bằng số điện thoại khi đặt hàng và tra cứu đơn.
_Avoid_: Anonymous user, visitor

**Khách hàng (Customer)**:
Người mua có tài khoản, có lịch sử đơn và sổ địa chỉ.
_Avoid_: User, member, client, buyer

**Nhân viên vận hành (Staff)**:
Người của doanh nghiệp xử lý đơn hàng, cập nhật tồn kho và xử lý đổi trả.
_Avoid_: Operator, employee, CS

**Quản trị viên (Admin)**:
Người của doanh nghiệp quản lý sản phẩm, giá, khuyến mãi, nhân viên và cấu hình hệ thống.
_Avoid_: Superuser, manager, owner
