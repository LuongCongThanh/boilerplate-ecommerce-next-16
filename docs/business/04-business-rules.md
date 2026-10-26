# 04. Quy tắc nghiệp vụ

> Trạng thái: **Bản nháp chờ review**. Mỗi quy tắc có mã `BR-xxx` để user story và test tham chiếu tới. Các mục **[Giả định]** cần xác nhận.
> Thuật ngữ dùng theo [GLOSSARY.md](../../GLOSSARY.md).

## 1. Danh mục hàng hoá

| Mã | Quy tắc |
|---|---|
| BR-CAT-01 | Mỗi Sản phẩm có ít nhất một Biến thể. Khách luôn mua Biến thể, không mua Sản phẩm. |
| BR-CAT-02 | Biến thể là tổ hợp duy nhất của **size × màu** trong một Sản phẩm. Không có hai Biến thể trùng size và màu. |
| BR-CAT-03 | Mỗi Biến thể có **mã SKU duy nhất toàn hệ thống**, viết bằng chữ in hoa tiếng Anh, số và dấu gạch ngang, ví dụ `TSHIRT-BASIC-WHT-M`. SKU không thay đổi sau khi đã có đơn. |
| BR-CAT-04 | Giá bán đặt ở cấp **Biến thể**. Giá là số nguyên VND, lớn hơn 0. |
| BR-CAT-05 | Ảnh gắn theo **màu** của Sản phẩm: mọi size cùng màu dùng chung bộ ảnh. |
| BR-CAT-06 | Cân nặng (gram) nhập ở cấp **Sản phẩm** và bắt buộc phải có để tính phí ship. |
| BR-CAT-07 | Sản phẩm có trạng thái `draft` (nháp), `active` (đang bán), `archived` (ngừng bán). Chỉ Sản phẩm `active` hiển thị trên storefront. |
| BR-CAT-08 | Sản phẩm `active` mà mọi Biến thể đều hết hàng vẫn hiển thị, kèm nhãn "Hết hàng", và không thêm vào giỏ được. |
| BR-CAT-09 | Không xoá cứng Sản phẩm hoặc Biến thể đã có trong đơn; chỉ chuyển sang `archived`. |
| BR-CAT-10 | Tên, mô tả Sản phẩm và tên danh mục chỉ có **tiếng Việt**. |

## 2. Giá và khuyến mãi

### 2.1. Giá khuyến mãi (Sale Price)

| Mã | Quy tắc |
|---|---|
| BR-PRC-01 | Giá khuyến mãi gắn với một Biến thể, có thời gian bắt đầu và kết thúc. Giá khuyến mãi phải **nhỏ hơn** giá bán. |
| BR-PRC-02 | Tại một thời điểm, mỗi Biến thể có tối đa **một** Giá khuyến mãi hiệu lực. |
| BR-PRC-03 | Giá áp dụng cho khách = Giá khuyến mãi nếu đang hiệu lực, ngược lại = giá bán. |
| BR-PRC-04 | Mức giảm của Giá khuyến mãi = `(giá bán − giá khuyến mãi) / giá bán`. Mức này quyết định quyền Đổi trả (BR-RET-03). |

### 2.2. Mã giảm giá (Voucher)

| Mã | Quy tắc |
|---|---|
| BR-VCH-01 | Mỗi Đơn hàng dùng **tối đa một** Voucher. |
| BR-VCH-02 | Voucher **cộng dồn** với Giá khuyến mãi: Voucher tính trên tạm tính đã áp Giá khuyến mãi. |
| BR-VCH-03 | Voucher có một trong hai kiểu: giảm **theo %** (có thể kèm mức giảm tối đa) hoặc giảm **số tiền cố định**. |
| BR-VCH-04 | Điều kiện của Voucher gồm: thời gian hiệu lực, giá trị đơn tối thiểu, tổng số lượt dùng, số lượt dùng tối đa cho mỗi khách. |
| BR-VCH-05 | Voucher chỉ giảm trên **tạm tính hàng hoá**, không giảm phí ship. |
| BR-VCH-06 | Số tiền giảm không vượt quá tạm tính hàng hoá; tổng tiền hàng sau giảm không âm. |
| BR-VCH-07 | "Mỗi khách" được xác định bằng tài khoản Khách hàng, hoặc bằng **số điện thoại** với Khách vãng lai. |
| BR-VCH-08 | Lượt dùng Voucher được tính khi đơn được tạo. Nếu đơn bị huỷ trước khi Đang giao, lượt dùng được **trả lại** **[Giả định]**. |
| BR-VCH-09 | Mã Voucher không phân biệt hoa thường, lưu dạng chữ in hoa, ví dụ `SALE10`. |

## 3. Tồn kho

| Mã | Quy tắc |
|---|---|
| BR-INV-01 | Tồn kho được quản lý theo **Biến thể × Kho**. MVP có một Kho. |
| BR-INV-02 | Số lượng bán được = Tồn kho thực tế − tổng Giữ hàng còn hiệu lực. Không bao giờ âm. |
| BR-INV-03 | Giỏ hàng **không** giữ hàng. Thêm vào giỏ không làm giảm số lượng bán được. |
| BR-INV-04 | Đơn **COD**: trừ Tồn kho ngay khi đặt đơn thành công. |
| BR-INV-05 | Đơn **thanh toán online**: tạo Giữ hàng có thời hạn **15 phút**. Thanh toán thành công thì chuyển Giữ hàng thành trừ Tồn kho. Hết hạn mà chưa thanh toán thì huỷ đơn và giải phóng Giữ hàng. |
| BR-INV-06 | Khi đặt đơn, nếu bất kỳ Dòng đơn hàng nào không đủ số lượng bán được thì **không tạo đơn** và báo cho khách Biến thể nào thiếu, còn bao nhiêu. |
| BR-INV-07 | Huỷ đơn trước khi Đang giao thì hàng được trả lại Tồn kho ngay. |
| BR-INV-08 | Đơn Hoàn hàng hoặc hàng Đổi trả: hàng chỉ được cộng lại Tồn kho khi Staff **xác nhận đã nhận và kiểm tra** hàng tại Kho **[Giả định]**. |
| BR-INV-09 | Mọi thay đổi Tồn kho đều được ghi lịch sử (loại thay đổi, số lượng, đơn liên quan, người thực hiện). |

## 4. Giỏ hàng

| Mã | Quy tắc |
|---|---|
| BR-CRT-01 | Giỏ hàng lưu ở server, cho cả Khách vãng lai và Khách hàng. |
| BR-CRT-02 | Giỏ của Khách vãng lai hết hạn sau **30 ngày** không hoạt động. |
| BR-CRT-03 | Khi Khách vãng lai đăng nhập, giỏ vãng lai được **gộp** vào giỏ tài khoản: Biến thể trùng thì cộng dồn số lượng, nhưng không vượt quá số lượng bán được. |
| BR-CRT-04 | Giá trong giỏ luôn là giá **hiện tại**. Nếu giá thay đổi so với lúc thêm vào giỏ, hệ thống thông báo cho khách. |
| BR-CRT-05 | Số lượng tối đa của một Biến thể trong một giỏ là **10** **[Giả định]**. |

## 5. Đặt hàng và tính tiền

| Mã | Quy tắc |
|---|---|
| BR-ORD-01 | Tổng tiền đơn = tạm tính hàng hoá (đã áp Giá khuyến mãi) − giảm giá Voucher + phí ship. |
| BR-ORD-02 | Dòng đơn hàng lưu **bản chụp** tên Sản phẩm, SKU, size, màu, đơn giá và mức giảm tại thời điểm đặt. Sửa Sản phẩm sau đó không làm đổi đơn cũ. |
| BR-ORD-03 | Mã đơn hiển thị cho khách có dạng `FS<YYMM>-<số thứ tự 6 chữ số>`, ví dụ `FS2610-000123` **[Giả định]**. |
| BR-ORD-04 | Địa chỉ giao hàng theo cấu trúc **2 cấp**: tỉnh/thành phố và phường/xã (theo sắp xếp đơn vị hành chính từ 07/2025), kèm địa chỉ chi tiết. |
| BR-ORD-05 | Chỉ huỷ **cả đơn**, không huỷ từng Dòng đơn hàng. Nếu một phần hàng không giao được, Staff liên hệ khách, huỷ đơn và tạo đơn mới. |
| BR-ORD-06 | Quy tắc huỷ và chuyển trạng thái xem [05-order-lifecycle.md](./05-order-lifecycle.md). |

## 6. Vận chuyển

| Mã | Quy tắc |
|---|---|
| BR-SHP-01 | Phí ship được lấy **theo thời gian thực** từ GHN, dựa trên địa chỉ giao và tổng cân nặng (cân nặng Sản phẩm × số lượng). Kích thước gói dùng giá trị mặc định cấu hình được. |
| BR-SHP-02 | Nếu API GHN lỗi hoặc quá thời gian chờ, dùng **phí ship dự phòng 35.000đ** để khách vẫn checkout được. Đơn được đánh dấu "phí ship dự phòng" để Staff theo dõi. |
| BR-SHP-03 | Đơn có tạm tính hàng hoá **sau khi trừ Voucher từ 500.000đ** được **miễn phí ship**; cửa hàng chịu phí GHN **[Giả định: tính sau Voucher]**. |
| BR-SHP-04 | Phí ship dự phòng và ngưỡng miễn phí ship do Admin cấu hình. |
| BR-SHP-05 | Vận đơn GHN được tạo tự động khi Staff chuyển đơn sang Đang giao (bàn giao cho GHN). |
| BR-SHP-06 | Trạng thái giao hàng được cập nhật từ GHN qua webhook và job đối soát định kỳ. |
| BR-SHP-07 | Với đơn COD, số tiền thu hộ = tổng tiền đơn. |

## 7. Thanh toán

| Mã | Quy tắc |
|---|---|
| BR-PAY-01 | Phương thức: **VNPay**, **MoMo**, **COD**. |
| BR-PAY-02 | Trạng thái thanh toán chỉ được xác nhận qua **thông báo server-to-server (IPN)** hoặc **job đối soát**, không bao giờ dựa vào trang khách được chuyển về (Return URL). |
| BR-PAY-03 | Một thông báo thanh toán nhận lặp lại nhiều lần chỉ được xử lý **một lần**. |
| BR-PAY-04 | Số tiền thanh toán nhận được phải khớp đúng tổng tiền đơn; không khớp thì không xác nhận và báo Staff. |
| BR-PAY-05 | Nếu nhận được tiền cho một đơn **đã bị huỷ** (ví dụ khách thanh toán sát lúc hết 15 phút), hệ thống **tự tạo yêu cầu Hoàn tiền** và báo Staff. |
| BR-PAY-06 | Giá trị đơn COD tối đa là **5.000.000đ** **[Giả định]**; vượt mức thì khách phải thanh toán online. |

## 8. Hoàn tiền

| Mã | Quy tắc |
|---|---|
| BR-REF-01 | Hoàn tiền luôn trả về **đúng cổng thanh toán** khách đã dùng. |
| BR-REF-02 | Phát sinh khi: huỷ đơn đã thanh toán online, Đổi trả được chấp nhận, hoặc trường hợp BR-PAY-05. |
| BR-REF-03 | MVP: Staff thực hiện hoàn tiền **thủ công** trên trang quản trị của VNPay hoặc MoMo, rồi ghi nhận "Đã hoàn tiền" trong back-office kèm mã giao dịch hoàn. |
| BR-REF-04 | Đơn COD bị huỷ trước khi giao: không phát sinh Hoàn tiền. Đơn COD Đổi trả: hoàn bằng chuyển khoản ngân hàng, Staff ghi nhận thủ công **[Giả định]**. |

## 9. Đổi trả

| Mã | Quy tắc |
|---|---|
| BR-RET-01 | Khách được yêu cầu Đổi trả trong **7 ngày** kể từ khi đơn **Đã giao**. Sau đó đơn chuyển sang **Hoàn tất** và hết quyền Đổi trả. |
| BR-RET-02 | Điều kiện: hàng **còn tag, chưa qua sử dụng**. |
| BR-RET-03 | Hàng có Giá khuyến mãi giảm **trên 50%** (BR-PRC-04) **không** được Đổi trả. |
| BR-RET-04 | MVP: khách gửi yêu cầu qua hotline hoặc Zalo; Staff ghi nhận yêu cầu trong back-office. |
| BR-RET-05 | "Đổi" hàng (đổi size, đổi màu) được xử lý như **trả hàng + tạo đơn mới** **[Giả định]**. |
| BR-RET-06 | Phí ship gửi trả: cửa hàng chịu nếu hàng lỗi hoặc giao sai, khách chịu trong các trường hợp còn lại **[Giả định]**. |

## 10. Thông báo

| Mã | Quy tắc |
|---|---|
| BR-NTF-01 | Email được gửi khi: đặt đơn thành công, thanh toán thành công, đơn bị huỷ, đơn Đang giao, đơn Đã giao, Hoàn tiền được ghi nhận. |
| BR-NTF-02 | Email gửi theo **ngôn ngữ khách đã chọn** (vi/en). Khách vãng lai: theo ngôn ngữ giao diện lúc đặt đơn. Tên Sản phẩm trong email luôn là tiếng Việt. |
| BR-NTF-03 | Khách vãng lai không nhập email thì không nhận email; vẫn tra cứu đơn được. |
