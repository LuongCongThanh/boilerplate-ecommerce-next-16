# 06. Tuân thủ pháp lý

> Trạng thái: **Bản nháp chờ review**.
>
> ⚠️ **Tài liệu này không phải tư vấn pháp lý.** Danh sách văn bản dưới đây được tổng hợp để định hướng thiết kế hệ thống. Các mục có nhãn **[Cần xác minh]** phải được pháp chế hoặc kế toán của doanh nghiệp kiểm tra lại hiệu lực và nội dung trước khi go-live.

## 1. Các văn bản liên quan

| Lĩnh vực | Văn bản | Ghi chú |
|---|---|---|
| Dữ liệu cá nhân | Nghị định 13/2023/NĐ-CP về bảo vệ dữ liệu cá nhân | Căn cứ đã chọn khi lập plan |
| Dữ liệu cá nhân | Luật Bảo vệ dữ liệu cá nhân 2025 và các văn bản hướng dẫn | **[Cần xác minh]** Luật này có thể đã thay thế phần lớn Nghị định 13 kể từ 01/01/2026. Cần đối chiếu lại các yêu cầu ở mục 2 |
| Hoá đơn điện tử | Nghị định 123/2020/NĐ-CP và các văn bản sửa đổi | **[Cần xác minh]** Quy định mới về thời điểm xuất hoá đơn cho từng giao dịch bán lẻ |
| Thương mại điện tử | Nghị định 52/2013/NĐ-CP (sửa đổi bởi Nghị định 85/2021/NĐ-CP) | Website bán hàng phải **thông báo với Bộ Công Thương**. **[Cần xác minh]** văn bản mới thay thế, nếu có |
| Bảo vệ người tiêu dùng | Luật Bảo vệ quyền lợi người tiêu dùng 2023 | Yêu cầu công khai thông tin, chính sách đổi trả và giải quyết khiếu nại |

## 2. Dữ liệu cá nhân

### 2.1. Dữ liệu thu thập

| Dữ liệu | Của ai | Mục đích |
|---|---|---|
| Họ tên, số điện thoại, địa chỉ giao hàng | Khách vãng lai, Khách hàng | Giao hàng, liên hệ về đơn |
| Email | Khách hàng (bắt buộc), Khách vãng lai (tuỳ chọn) | Đăng nhập, gửi thông báo đơn |
| Mật khẩu (chỉ lưu dạng băm) | Khách hàng | Xác thực |
| Lịch sử đơn hàng | Khách vãng lai, Khách hàng | Thực hiện hợp đồng mua bán, kế toán |
| Ngôn ngữ đã chọn | Khách hàng | Hiển thị và gửi email đúng ngôn ngữ |
| Địa chỉ IP, thông tin phiên | Mọi người dùng | Bảo mật, chống gian lận |

Hệ thống **không** lưu thông tin thẻ hoặc tài khoản thanh toán; phần này do VNPay và MoMo xử lý.

### 2.2. Yêu cầu chức năng

| Mã | Yêu cầu |
|---|---|
| CMP-01 | **Xin đồng ý** xử lý dữ liệu cá nhân khi đăng ký tài khoản và khi checkout: một checkbox **không được tick sẵn**, kèm liên kết tới chính sách bảo mật. |
| CMP-02 | Lưu **bằng chứng đồng ý**: phiên bản chính sách, thời điểm, kênh (đăng ký / checkout), và người đồng ý. |
| CMP-03 | Đồng ý nhận **email marketing** là một lựa chọn **riêng**, không gộp với đồng ý xử lý dữ liệu để giao hàng. MVP chưa gửi email marketing nhưng vẫn lưu lựa chọn này. |
| CMP-04 | Khách hàng xem và sửa được dữ liệu cá nhân của mình trong tài khoản. |
| CMP-05 | Khách được **yêu cầu xoá dữ liệu**. Hệ thống **ẩn danh** thông tin cá nhân (tên, điện thoại, email, địa chỉ) và giữ lại dữ liệu đơn hàng cần cho kế toán, thuế. |
| CMP-06 | Yêu cầu xoá được xử lý trong thời hạn quy định **[Cần xác minh]**, hệ thống ghi lại thời điểm nhận và thời điểm hoàn thành. |
| CMP-07 | Mọi lượt Staff xem thông tin chi tiết của khách đều được ghi lịch sử. |
| CMP-08 | Khi triển khai lên AWS region Singapore (dữ liệu ra ngoài lãnh thổ Việt Nam), doanh nghiệp phải lập **hồ sơ đánh giá tác động chuyển dữ liệu cá nhân ra nước ngoài** theo quy định **[Cần xác minh]**. |
| CMP-09 | Có quy trình thông báo khi xảy ra **sự cố lộ lọt dữ liệu**, trong thời hạn quy định **[Cần xác minh]**. |

## 3. Hoá đơn điện tử

- **MVP**: hệ thống **không** tích hợp hoá đơn điện tử. Kế toán xuất hoá đơn thủ công bằng phần mềm hoá đơn bên ngoài.
- Để hỗ trợ kế toán, back-office cung cấp **danh sách đơn đã thu tiền theo ngày**, xuất được ra file (CSV/Excel), kèm thông tin xuất hoá đơn nếu khách yêu cầu.
- Checkout cho phép khách **yêu cầu xuất hoá đơn công ty** (tên công ty, mã số thuế, địa chỉ, email nhận hoá đơn) **[Giả định]**.
- **Giai đoạn 2**: tích hợp tự động với nhà cung cấp hoá đơn điện tử.
- **[Cần xác minh]** với kế toán: quy định hiện hành có cho phép xuất hoá đơn tổng hợp cuối ngày cho bán lẻ hay bắt buộc xuất theo từng giao dịch. Nếu bắt buộc theo từng giao dịch, cần cân nhắc đưa tích hợp lên MVP.

## 4. Thông tin bắt buộc công khai trên website

Đây là phần nội dung của Frontend, nhưng Backend phải cho phép Admin cấu hình:

- Thông tin doanh nghiệp: tên, địa chỉ, mã số thuế, số điện thoại, email.
- Chính sách: bảo mật, đổi trả, vận chuyển, thanh toán, giải quyết khiếu nại.
- Logo "Đã thông báo Bộ Công Thương" sau khi hoàn thành thủ tục.
