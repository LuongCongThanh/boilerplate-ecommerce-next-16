# Cửa hàng thời trang B2C (Fashion Store)

Website bán lẻ thời trang của một doanh nghiệp duy nhất cho người mua tại Việt Nam. Thuật ngữ được ghi song ngữ Việt / Anh; tên tiếng Anh là tên dùng trong code và tài liệu kiến trúc.

## Sản phẩm (Catalog)

**Danh mục (Category)**:
Một nhóm Sản phẩm để Người mua duyệt, có thể lồng nhau thành cây, ví dụ "Áo" > "Áo thun".
_Avoid_: Collection, nhóm hàng, catalog

**Sản phẩm (Product)**:
Một mẫu hàng chung mà Người mua nhìn thấy trên trang danh sách, ví dụ "Áo thun Basic". Người mua không mua trực tiếp Sản phẩm mà mua một Biến thể của nó.
_Avoid_: Item, mặt hàng, hàng hoá

**Biến thể (Variant)**:
Một tổ hợp cụ thể của size và màu thuộc một Sản phẩm. Mỗi Biến thể có Mã SKU, Giá bán và Tồn kho riêng, và là đơn vị mà Người mua thực sự mua.
_Avoid_: Option, phân loại, model

**Mã SKU (SKU)**:
Mã định danh duy nhất của một Biến thể.
_Avoid_: Product code, mã hàng

## Tồn kho (Inventory)

**Kho (Warehouse)**:
Một địa điểm vật lý nơi hàng được lưu trữ và xuất đi giao. Ở giai đoạn MVP chỉ có một Kho.
_Avoid_: Chi nhánh, store, location

**Tồn kho (Stock)**:
Số lượng thực có của một Biến thể trong một Kho, gồm cả phần đang bị Giữ hàng.
_Avoid_: Inventory count, số lượng, tồn thực tế

**Số lượng bán được (Available Quantity)**:
Phần Tồn kho mà Người mua còn mua được, bằng Tồn kho trừ các Giữ hàng còn hiệu lực. Không bao giờ âm.
_Avoid_: Sellable stock, tồn khả dụng

**Giữ hàng (Stock Reservation)**:
Phần Tồn kho bị tạm khoá cho một đơn chưa thanh toán online, có thời hạn 15 phút. Hết hạn mà chưa thanh toán thì phần giữ này được giải phóng và trở lại Số lượng bán được.
_Avoid_: Hold, lock, tạm giữ

## Giá và khuyến mãi (Pricing & Promotions)

**Giá bán (List Price)**:
Giá thường của một Biến thể, khi không có Giá khuyến mãi.
_Avoid_: Original price, giá gốc, giá niêm yết

**Giá khuyến mãi (Sale Price)**:
Giá giảm gắn trực tiếp vào một Biến thể trong một khoảng thời gian, áp dụng tự động mà Người mua không cần nhập mã.
_Avoid_: Discount price, giá sale, promotion

**Giá áp dụng (Effective Price)**:
Giá Người mua thực trả cho một Biến thể tại một thời điểm: Giá khuyến mãi nếu đang hiệu lực, ngược lại là Giá bán.
_Avoid_: Final price, current price, giá cuối

**Mã giảm giá (Voucher)**:
Mã mà Người mua nhập khi checkout để được giảm trên toàn đơn, theo % hoặc số tiền cố định, có điều kiện và giới hạn lượt dùng. Mỗi Đơn hàng dùng tối đa một Voucher, và Voucher được cộng dồn với Giá khuyến mãi.
_Avoid_: Coupon, promo code, promotion

## Đơn hàng (Ordering)

**Giỏ hàng (Cart)**:
Danh sách Biến thể và số lượng mà một Người mua định mua, lưu ở server. Giỏ hàng không Giữ hàng và luôn hiển thị Giá áp dụng hiện tại.
_Avoid_: Basket, bag, túi hàng

**Đơn hàng (Order)**:
Một lần mua hàng của một Người mua, gồm một hay nhiều Biến thể, giao tới một địa chỉ và có một Phương thức thanh toán. Đơn chỉ được huỷ nguyên đơn, không huỷ từng phần.
_Avoid_: Purchase, transaction, giao dịch

**Mã đơn (Order Code)**:
Mã hiển thị cho Người mua để nhận diện và tra cứu một Đơn hàng. Không đoán được và không cho biết thứ tự hay số lượng đơn.
_Avoid_: Order number, order ID, số đơn

**Dòng đơn hàng (Order Line)**:
Một Biến thể kèm số lượng và đơn giá tại thời điểm đặt, nằm trong một Đơn hàng.
_Avoid_: Order item, cart item

**Tạm tính (Subtotal)**:
Tổng Giá áp dụng nhân số lượng của các Dòng đơn hàng, trước khi trừ Voucher và cộng phí ship.
_Avoid_: Items total, tổng tiền hàng

**Cờ cần xử lý (Attention Flag)**:
Một vấn đề trên Đơn hàng mà Staff phải xử lý tay, ví dụ tiền về sai số tiền hoặc tạo Vận đơn thất bại. Cờ được gỡ khi Staff xử lý xong.
_Avoid_: Alert, cảnh báo, ticket

**Hoàn tất (Completed)**:
Trạng thái cuối của Đơn hàng, đạt được 7 ngày sau khi Đã giao, khi không còn yêu cầu Đổi trả nào đang mở. Đây là mốc hết quyền yêu cầu Đổi trả và là lúc doanh thu của đơn được chốt.
_Avoid_: Closed, finished, done

**Hoàn hàng (Returned to Sender)**:
Trạng thái của Đơn hàng khi giao thất bại và hãng vận chuyển trả hàng về Kho.
_Avoid_: Return, đổi trả, failed delivery

**Đổi trả (Return)**:
Yêu cầu của Người mua gửi lại hàng đã nhận trong vòng 7 ngày kể từ khi Đã giao, với hàng còn tag và chưa qua sử dụng. Hàng có Giá khuyến mãi giảm trên 50% không được Đổi trả.
_Avoid_: Refund, hoàn hàng, RMA

**Hoàn tiền (Refund)**:
Việc trả lại tiền cho Người mua: về đúng Cổng thanh toán đã nhận khoản tiền đó với đơn online, hoặc bằng chuyển khoản ngân hàng với đơn COD. Phát sinh khi huỷ một đơn đã thanh toán online, khi Đổi trả được chấp nhận, hoặc khi tiền về cho một Đơn hàng không còn chờ thanh toán.
_Avoid_: Chargeback, reimbursement

## Thanh toán (Payments)

**Phương thức thanh toán (Payment Method)**:
Cách trả tiền cho một Đơn hàng, chốt lúc đặt đơn: COD (trả tiền mặt khi nhận hàng) hoặc online (trả trước qua một Cổng thanh toán).
_Avoid_: Payment type, hình thức thanh toán

**Cổng thanh toán (Payment Gateway)**:
Nhà cung cấp nhận tiền online cho cửa hàng, hiện là VNPay và MoMo. Người mua chọn Cổng thanh toán ở mỗi lần trả tiền, nên một Đơn hàng online có thể thử qua nhiều Cổng.
_Avoid_: Provider, PSP, ví

**Thanh toán (Payment)**:
Một lần trả tiền cho một Đơn hàng qua một Cổng thanh toán, hoặc khoản thu tiền mặt của một đơn COD. Một Đơn hàng online có thể có nhiều Thanh toán, vì mỗi lần thử là một Thanh toán mới.
_Avoid_: Transaction, giao dịch

**Đối soát (Reconciliation)**:
Việc hệ thống chủ động hỏi Cổng thanh toán hoặc hãng vận chuyển về trạng thái của các Thanh toán và Vận đơn còn treo, để không phụ thuộc hoàn toàn vào thông báo từ họ.
_Avoid_: Sync, polling, quyết toán

## Vận chuyển (Shipping)

**Vận đơn (Shipment)**:
Đơn giao hàng tạo ở hãng vận chuyển (GHN) cho một Đơn hàng, có mã để theo dõi hành trình.
_Avoid_: Delivery, đơn GHN, tracking

**Phí ship dự phòng (Fallback Shipping Fee)**:
Phí ship cố định áp dụng cho Đơn hàng khi không lấy được phí từ hãng vận chuyển.
_Avoid_: Default fee, phí mặc định

## Người dùng (Actors)

**Người mua (Shopper)**:
Khách vãng lai hoặc Khách hàng, dùng khi một quy tắc áp dụng cho cả hai.
_Avoid_: Buyer, user, "khách" đứng một mình

**Khách vãng lai (Guest)**:
Người mua không có Tài khoản, được nhận diện bằng số điện thoại khi đặt hàng và tra cứu đơn.
_Avoid_: Anonymous user, visitor

**Khách hàng (Customer)**:
Người mua có Tài khoản, có lịch sử đơn và sổ địa chỉ.
_Avoid_: User, member, client, buyer

**Nhân viên vận hành (Staff)**:
Người của doanh nghiệp xử lý Đơn hàng, cập nhật Tồn kho và xử lý Đổi trả.
_Avoid_: Operator, employee, CS

**Quản trị viên (Admin)**:
Người của doanh nghiệp quản lý Sản phẩm, giá, khuyến mãi, Staff và cấu hình hệ thống.
_Avoid_: Superuser, manager, owner

**Tài khoản (Account)**:
Danh tính đăng nhập của một Khách hàng, Staff hoặc Admin. Mỗi email thuộc tối đa một Tài khoản, nên một người vừa là Staff vừa muốn mua hàng phải dùng hai email khác nhau.
_Avoid_: User, profile, login
