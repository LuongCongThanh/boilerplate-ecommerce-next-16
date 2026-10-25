# 02. Vai trò người dùng và phân quyền

> Trạng thái: **Bản nháp chờ review**. Thuật ngữ dùng theo [GLOSSARY.md](../../GLOSSARY.md).

## 1. Các vai trò

| Vai trò | Mã (code) | Mô tả | Kênh sử dụng |
|---|---|---|---|
| Khách vãng lai | `guest` | Người mua không có tài khoản, được nhận diện bằng số điện thoại khi đặt hàng và tra cứu đơn | Storefront |
| Khách hàng | `customer` | Người mua có tài khoản | Storefront |
| Nhân viên vận hành | `staff` | Người của doanh nghiệp, xử lý công việc hằng ngày | Back-office |
| Quản trị viên | `admin` | Người của doanh nghiệp, quản lý cấu hình và nhân sự | Back-office |

Hai quy tắc chung:

- Mỗi tài khoản nội bộ có đúng một vai trò `staff` hoặc `admin`. `admin` có toàn bộ quyền của `staff`.
- Tài khoản nội bộ **không** dùng để mua hàng. Nhân viên muốn mua hàng thì đăng ký một tài khoản Khách hàng riêng.

## 2. Nhận diện Khách vãng lai

- Khách vãng lai có giỏ hàng gắn với trình duyệt (cookie), hết hạn sau 30 ngày không hoạt động.
- Khi đặt hàng, Khách vãng lai bắt buộc nhập **họ tên, số điện thoại, địa chỉ giao hàng**. Email là tuỳ chọn; có email thì nhận email thông báo.
- Tra cứu đơn bằng **mã đơn + số điện thoại đặt hàng**. Hai thông tin phải khớp nhau.
- Nếu sau đó Khách vãng lai đăng ký tài khoản bằng **cùng email** đã dùng khi đặt hàng, các đơn cũ có email đó được gắn vào tài khoản mới **[Giả định]**.

## 3. Ma trận phân quyền

Ký hiệu: ✅ được phép · ⚠️ được phép có điều kiện (xem ghi chú) · — không được phép

### 3.1. Storefront

| Hành động | Guest | Customer |
|---|---|---|
| Xem, tìm kiếm, lọc Sản phẩm | ✅ | ✅ |
| Thêm, sửa, xoá giỏ hàng | ✅ | ✅ |
| Đặt hàng | ✅ | ✅ |
| Áp Voucher | ✅ | ✅ |
| Xem chi tiết đơn của mình | ⚠️ (1) | ✅ |
| Tự huỷ đơn | ⚠️ (1)(2) | ⚠️ (2) |
| Lưu sổ địa chỉ | — | ✅ |
| Xem lịch sử đơn | — | ✅ |
| Đổi mật khẩu, cập nhật hồ sơ, chọn ngôn ngữ | — | ✅ |
| Yêu cầu xoá hoặc ẩn danh dữ liệu cá nhân | ⚠️ (3) | ✅ |

1. Sau khi tra cứu đúng mã đơn và số điện thoại.
2. Chỉ khi đơn còn ở trạng thái **trước Đang đóng gói** (xem [05-order-lifecycle.md](./05-order-lifecycle.md)).
3. Gửi yêu cầu qua kênh hỗ trợ, Staff xác minh danh tính rồi xử lý.

### 3.2. Back-office

| Hành động | Staff | Admin |
|---|---|---|
| Xem danh sách và chi tiết Đơn hàng | ✅ | ✅ |
| Xác nhận đơn, chuyển Đang đóng gói, bàn giao vận chuyển | ✅ | ✅ |
| Huỷ đơn (mọi trạng thái được phép huỷ) | ✅ | ✅ |
| Ghi nhận Hoàn tiền thủ công | ✅ | ✅ |
| Ghi nhận Đổi trả | ✅ | ✅ |
| Nhập kho, điều chỉnh Tồn kho (có ghi lý do) | ✅ | ✅ |
| Xem thông tin Khách hàng | ✅ | ✅ |
| Xử lý yêu cầu xoá hoặc ẩn danh dữ liệu | ✅ | ✅ |
| Tạo, sửa, ẩn Sản phẩm và Biến thể | — | ✅ |
| Đặt giá bán và Giá khuyến mãi | — | ✅ |
| Tạo, sửa, vô hiệu Voucher | — | ✅ |
| Quản lý tài khoản Staff | — | ✅ |
| Cấu hình hệ thống (phí ship dự phòng, ngưỡng miễn phí ship, thời gian giữ hàng…) | — | ✅ |
| Xem báo cáo doanh thu | — | ✅ |

## 4. Quy tắc kiểm soát

- Mọi thao tác ghi trên back-office được **ghi lịch sử**: ai làm, lúc nào, giá trị trước và sau.
- Điều chỉnh Tồn kho thủ công bắt buộc nhập lý do (ví dụ: kiểm kê, hàng lỗi, hàng mẫu).
- Huỷ đơn từ trạng thái Đang đóng gói trở đi bắt buộc nhập lý do.
- Tài khoản Staff bị vô hiệu hoá thì mọi phiên đăng nhập của tài khoản đó mất hiệu lực ngay.
