# 02. Vai trò người dùng và phân quyền

> Trạng thái: **Bản nháp chờ review**. Thuật ngữ dùng theo [GLOSSARY.md](../../GLOSSARY.md).

## 1. Các vai trò

| Vai trò | Mã (code) | Mô tả | Kênh sử dụng |
|---|---|---|---|
| Khách vãng lai | `guest` | Người mua không có Tài khoản, được nhận diện bằng số điện thoại khi đặt hàng và tra cứu đơn | Storefront |
| Khách hàng | `customer` | Người mua có Tài khoản | Storefront |
| Nhân viên vận hành | `staff` | Người của doanh nghiệp, xử lý công việc hằng ngày | Back-office |
| Quản trị viên | `admin` | Người của doanh nghiệp, quản lý cấu hình và nhân sự | Back-office |

Ba quy tắc chung:

- Mỗi Tài khoản nội bộ có đúng một vai trò `staff` hoặc `admin`. `admin` có toàn bộ quyền của `staff`.
- Mỗi email chỉ thuộc **một** Tài khoản, dù là Khách hàng, Staff hay Admin.
- Tài khoản nội bộ **không** dùng để mua hàng. Nhân viên muốn mua hàng thì đăng ký một Tài khoản Khách hàng riêng bằng **email khác**. Đăng nhập storefront (kể cả bằng Google) với email của Tài khoản nội bộ bị từ chối với thông báo lỗi chung.

## 2. Nhận diện Khách vãng lai

- Khách vãng lai có Giỏ hàng gắn với trình duyệt (cookie), hết hạn sau 30 ngày không hoạt động.
- Khi đặt hàng, Khách vãng lai bắt buộc nhập **họ tên, số điện thoại, địa chỉ giao hàng**. Email là tuỳ chọn; có email thì nhận email thông báo.
- Ngay sau khi đặt hàng, Khách vãng lai được xem, thanh toán và huỷ đơn vừa đặt trong **30 phút** mà không phải tra cứu lại.
- Sau đó, tra cứu đơn bằng **Mã đơn + số điện thoại đặt hàng**. Hai thông tin phải khớp nhau. Mỗi lần tra cứu đúng cho phép thao tác với đơn đó trong 30 phút.
- Nếu sau đó Khách vãng lai đăng ký Tài khoản bằng **cùng email** đã dùng khi đặt hàng, các đơn cũ có email đó được gắn vào Tài khoản mới, nhưng **chỉ sau khi email đã được xác thực**. Không gắn theo số điện thoại, vì số điện thoại không được xác thực.

## 3. Ma trận phân quyền

Ký hiệu: ✅ được phép · ⚠️ được phép có điều kiện (xem ghi chú) · — không được phép

### 3.1. Storefront

| Hành động | Guest | Customer |
|---|---|---|
| Xem, tìm kiếm, lọc Sản phẩm | ✅ | ✅ |
| Thêm, sửa, xoá Giỏ hàng | ✅ | ✅ |
| Đặt hàng | ✅ | ✅ |
| Áp Voucher | ✅ | ✅ |
| Xem chi tiết đơn của mình | ⚠️ (1) | ✅ |
| Tự huỷ đơn | ⚠️ (1)(2) | ⚠️ (2) |
| Lưu sổ địa chỉ | — | ✅ |
| Xem lịch sử đơn | — | ✅ |
| Đổi mật khẩu, cập nhật hồ sơ, chọn ngôn ngữ | — | ✅ |
| Yêu cầu xoá hoặc ẩn danh dữ liệu cá nhân | ⚠️ (3) | ✅ |

1. Ngay sau khi đặt đơn, hoặc sau khi tra cứu đúng Mã đơn và số điện thoại; có hiệu lực 30 phút (mục 2).
2. Chỉ khi đơn còn ở trạng thái **trước Đang đóng gói** (xem [05-order-lifecycle.md](./05-order-lifecycle.md)).
3. Gửi yêu cầu qua kênh hỗ trợ, Staff xác minh danh tính rồi xử lý.

### 3.2. Back-office

| Hành động | Staff | Admin |
|---|---|---|
| Xem danh sách và chi tiết Đơn hàng | ✅ | ✅ |
| Xác nhận đơn, chuyển Đang đóng gói, bàn giao vận chuyển | ✅ | ✅ |
| Huỷ đơn (mọi trạng thái được phép huỷ) | ✅ | ✅ |
| Xem và gỡ Cờ cần xử lý trên Đơn hàng | ✅ | ✅ |
| Ghi nhận Hoàn tiền thủ công | ✅ | ✅ |
| Ghi nhận Đổi trả | ✅ | ✅ |
| Nhập kho, điều chỉnh Tồn kho (có ghi lý do) | ✅ | ✅ |
| Xem thông tin Khách hàng | ✅ | ✅ |
| Xử lý yêu cầu xoá hoặc ẩn danh dữ liệu | ✅ | ✅ |
| Tạo, sửa, ẩn Sản phẩm và Biến thể | — | ✅ |
| Đặt giá bán và Giá khuyến mãi | — | ✅ |
| Tạo, sửa, vô hiệu Voucher | — | ✅ |
| Quản lý Tài khoản Staff | — | ✅ |
| Cấu hình vận hành: Phí ship dự phòng, ngưỡng miễn phí ship, hạn mức COD (thời gian Giữ hàng là cố định, không cấu hình) | — | ✅ |
| Xem báo cáo doanh thu | — | ✅ |

## 4. Quy tắc kiểm soát

- Mọi thao tác ghi trên back-office được **ghi lịch sử**: ai làm, lúc nào, giá trị trước và sau.
- Điều chỉnh Tồn kho thủ công bắt buộc nhập lý do (ví dụ: kiểm kê, hàng lỗi, hàng mẫu).
- Huỷ đơn từ trạng thái Đang đóng gói trở đi bắt buộc nhập lý do.
- Tài khoản Staff bị vô hiệu hoá thì mọi phiên đăng nhập của tài khoản đó mất hiệu lực ngay.
