# 03. User stories

> Trạng thái: **Bản nháp chờ review**. Chỉ gồm phạm vi **MVP**.
> Mỗi story có tiêu chí nghiệm thu (AC) viết theo dạng *Cho trước / Khi / Thì*, và tham chiếu tới quy tắc `BR-xxx` trong [04-business-rules.md](./04-business-rules.md).
> Độ ưu tiên: **P1** bắt buộc cho MVP, **P2** nên có trong MVP.

## Danh sách epic

| Epic | Tên | Vai trò chính |
|---|---|---|
| E1 | Duyệt và tìm kiếm Sản phẩm | Guest, Customer |
| E2 | Giỏ hàng | Guest, Customer |
| E3 | Checkout và thanh toán | Guest, Customer |
| E4 | Theo dõi và huỷ đơn | Guest, Customer |
| E5 | Tài khoản Khách hàng | Customer |
| E6 | Xử lý Đơn hàng | Staff |
| E7 | Tồn kho | Staff |
| E8 | Quản lý Sản phẩm và Danh mục | Admin |
| E9 | Khuyến mãi | Admin |
| E10 | Quản trị hệ thống | Admin |
| E11 | Dữ liệu cá nhân | Guest, Customer, Staff |

---

## E1. Duyệt và tìm kiếm Sản phẩm

### US-101 · Xem danh sách Sản phẩm theo danh mục · P1
**Là** khách, **tôi muốn** xem Sản phẩm theo danh mục **để** tìm món mình cần.

- AC1: Cho trước danh mục "Áo thun" có 30 Sản phẩm `active`, khi khách mở danh mục, thì thấy danh sách có phân trang, mỗi Sản phẩm hiện ảnh, tên, giá thấp nhất trong các Biến thể (BR-PRC-03) và giá gốc nếu đang có Giá khuyến mãi.
- AC2: Sản phẩm `draft` hoặc `archived` không xuất hiện (BR-CAT-07).
- AC3: Sản phẩm hết hàng mọi Biến thể vẫn hiện, kèm nhãn "Hết hàng" (BR-CAT-08).

### US-102 · Lọc và sắp xếp · P1
**Là** khách, **tôi muốn** lọc theo size, màu, khoảng giá và sắp xếp **để** thu hẹp kết quả.

- AC1: Khi chọn size M và màu Trắng, thì chỉ hiện Sản phẩm có **ít nhất một Biến thể** size M màu Trắng còn hàng.
- AC2: Sắp xếp được theo: mới nhất, giá tăng dần, giá giảm dần, bán chạy.
- AC3: Lọc theo giá dùng giá áp dụng cho khách (đã tính Giá khuyến mãi).

### US-103 · Tìm kiếm theo tên · P1
**Là** khách, **tôi muốn** gõ tên Sản phẩm **để** tìm nhanh.

- AC1: Gõ "ao thun" (không dấu) cho kết quả giống "áo thun".
- AC2: Gõ một phần tên, ví dụ "basic", vẫn ra Sản phẩm "Áo thun Basic cổ tròn".
- AC3: Không có kết quả thì hiển thị thông báo và gợi ý danh mục.

### US-104 · Xem chi tiết Sản phẩm · P1
**Là** khách, **tôi muốn** xem chi tiết và chọn size, màu **để** quyết định mua.

- AC1: Chọn màu thì đổi bộ ảnh theo màu (BR-CAT-05).
- AC2: Chọn size × màu thì hiện đúng giá, SKU và trạng thái còn hàng của Biến thể đó.
- AC3: Tổ hợp size × màu không tồn tại hoặc hết hàng thì không chọn được để thêm vào giỏ.

---

## E2. Giỏ hàng

### US-201 · Thêm vào giỏ · P1
- AC1: Cho trước Biến thể còn 3, khi khách thêm 2, thì giỏ có 2. Thêm tiếp 2 thì báo chỉ còn 3 và giỏ giữ ở mức 3.
- AC2: Không vượt quá 10 cho mỗi Biến thể (BR-CRT-05).
- AC3: Thêm vào giỏ không làm giảm số lượng bán được (BR-INV-03).

### US-202 · Xem và sửa giỏ · P1
- AC1: Giỏ hiện giá **hiện tại** của từng Biến thể. Nếu giá đã đổi so với lúc thêm, hiện thông báo (BR-CRT-04).
- AC2: Biến thể đã hết hàng hoặc bị `archived` được đánh dấu và không cho checkout cho tới khi khách xoá khỏi giỏ.

### US-203 · Giữ giỏ cho Khách vãng lai · P1
- AC1: Khách vãng lai thêm hàng, đóng trình duyệt, quay lại sau 3 ngày vẫn thấy giỏ.
- AC2: Sau 30 ngày không hoạt động thì giỏ bị xoá (BR-CRT-02).

### US-204 · Gộp giỏ khi đăng nhập · P1
- AC1: Cho trước giỏ vãng lai có Biến thể A × 2, giỏ tài khoản có A × 1 và B × 1, khi đăng nhập, thì giỏ tài khoản có A × 3 và B × 1 (BR-CRT-03).
- AC2: Nếu A chỉ còn 2 thì A được giữ ở mức 2 và khách được thông báo.

---

## E3. Checkout và thanh toán

### US-301 · Checkout không cần tài khoản · P1
**Là** Khách vãng lai, **tôi muốn** đặt hàng mà không phải đăng ký **để** mua nhanh.

- AC1: Bắt buộc nhập họ tên, số điện thoại, tỉnh/thành, phường/xã, địa chỉ chi tiết; email tuỳ chọn.
- AC2: Số điện thoại phải là số di động Việt Nam hợp lệ.
- AC3: Bắt buộc tick đồng ý xử lý dữ liệu cá nhân, checkbox không tick sẵn (CMP-01).
- AC4: Ngay sau khi đặt đơn, Khách vãng lai xem, thanh toán và huỷ được đơn vừa đặt trong 30 phút mà không phải tra cứu lại (xem [02-actors-permissions.md](./02-actors-permissions.md) mục 2).

### US-302 · Checkout với tài khoản · P1
- AC1: Khách hàng chọn được địa chỉ từ sổ địa chỉ hoặc nhập địa chỉ mới (có tuỳ chọn lưu vào sổ).
- AC2: Thông tin liên hệ được điền sẵn từ hồ sơ.

### US-303 · Xem phí ship · P1
- AC1: Khi khách chọn xong phường/xã, hệ thống hiện phí ship lấy từ GHN (BR-SHP-01).
- AC2: Cho trước API GHN lỗi, thì hiện Phí ship dự phòng (mặc định 35.000đ) và khách vẫn đặt hàng được (BR-SHP-02).
- AC3: Đơn từ 500.000đ (sau Voucher) thì phí ship = 0đ (BR-SHP-03).

### US-304 · Áp Voucher · P1
- AC1: Nhập `sale10` hay `SALE10` đều nhận (BR-VCH-09).
- AC2: Voucher hết hạn, hết lượt, chưa đủ giá trị đơn tối thiểu, hoặc Người mua đã dùng hết lượt của mình (đếm theo Tài khoản hoặc số điện thoại, BR-VCH-07) thì báo lý do cụ thể.
- AC3: Đã có một Voucher, nhập Voucher thứ hai thì Voucher mới **thay thế** Voucher cũ (BR-VCH-01).
- AC4: Voucher không giảm phí ship (BR-VCH-05).

### US-305 · Đặt đơn COD · P1
- AC1: Cho trước giỏ hợp lệ và tổng tiền ≤ hạn mức COD (mặc định 5.000.000đ), khi chọn COD và đặt hàng, thì đơn ở trạng thái Chờ xác nhận, Tồn kho bị trừ ngay (BR-INV-04), khách thấy Mã đơn.
- AC2: Tổng tiền vượt hạn mức COD thì không cho chọn COD (BR-PAY-06).
- AC3: Có email thì nhận email "Đặt đơn thành công".

### US-306 · Thanh toán VNPay / MoMo · P1
- AC1: Khi chọn thanh toán online và đặt hàng, đơn ở Chờ thanh toán, hàng được Giữ 15 phút (BR-INV-05). Người mua chọn Cổng thanh toán VNPay hoặc MoMo rồi được chuyển sang trang của Cổng đó.
- AC2: Thanh toán thành công thì đơn chuyển sang Chờ xác nhận **chỉ khi** hệ thống nhận IPN hoặc Đối soát thành công, không dựa vào việc khách quay lại trang (BR-PAY-02).
- AC3: Khách quay lại trang trước khi IPN tới thì thấy trạng thái "Đang xác nhận thanh toán" và trang tự cập nhật.
- AC4: Quá 15 phút chưa thanh toán thì đơn bị huỷ và hàng được giải phóng (T4).
- AC5: Thanh toán thất bại thì Người mua được thử lại, bằng cùng Cổng hoặc Cổng khác, cho tới phút thứ 10 kể từ khi đặt đơn (BR-PAY-01, BR-INV-05).
- AC6: Đơn online chưa thanh toán không nhận email "Đặt đơn thành công"; thanh toán thành công thì nhận email "Thanh toán thành công" (BR-NTF-01).

### US-307 · Hết hàng khi đặt đơn · P1
- AC1: Cho trước hai khách cùng đặt Biến thể cuối cùng, thì chỉ một đơn thành công; khách còn lại được báo hết hàng và không có đơn nào được tạo cho khách đó (BR-INV-06).

### US-308 · Giá thay đổi khi đặt đơn · P1
- AC1: Cho trước Người mua đã xem tổng 450.000đ ở bước tính thử, khi Giá khuyến mãi vừa hết hạn và tổng tính lại là 520.000đ, thì đơn **không** được tạo và Người mua thấy bảng tính mới để xác nhận lại (BR-ORD-07).
- AC2: Tương tự khi Voucher vừa hết lượt hoặc phí ship thay đổi.

---

## E4. Theo dõi và huỷ đơn

### US-401 · Khách vãng lai tra cứu đơn · P1
- AC1: Nhập đúng mã đơn và số điện thoại thì xem được chi tiết đơn và trạng thái.
- AC2: Sai một trong hai thì báo "Không tìm thấy đơn", không tiết lộ thông tin nào khác.
- AC3: Giới hạn số lần tra cứu sai theo IP để chống dò mã đơn.

### US-402 · Khách hàng xem lịch sử đơn · P1
- AC1: Danh sách đơn sắp xếp mới nhất trước, có lọc theo trạng thái.
- AC2: Chi tiết đơn hiện Dòng đơn hàng theo **bản chụp** lúc đặt (BR-ORD-02), mã vận đơn GHN khi có.

### US-403 · Khách tự huỷ đơn · P1
- AC1: Đơn ở Chờ thanh toán, Chờ xác nhận hoặc Đã xác nhận thì có nút huỷ.
- AC2: Đơn từ Đang đóng gói trở đi thì không có nút huỷ, hiển thị hướng dẫn liên hệ hotline.
- AC3: Huỷ đơn đã thanh toán online thì khách được báo tiền sẽ được hoàn về đúng Cổng thanh toán đã nhận tiền (BR-REF-01).

---

## E5. Tài khoản Khách hàng

### US-501 · Đăng ký bằng email · P1
- AC1: Email chưa tồn tại, mật khẩu đạt yêu cầu tối thiểu, tick đồng ý dữ liệu cá nhân thì tạo tài khoản và gửi email xác thực.
- AC2: Email đã tồn tại (kể cả email của Tài khoản Staff/Admin) thì báo lỗi chung, không xác nhận email đó có tồn tại hay không **[Giả định]**.
- AC3: Sau khi email được xác thực, các đơn đặt như Khách vãng lai bằng cùng email được gắn vào Tài khoản (xem [02-actors-permissions.md](./02-actors-permissions.md) mục 2).

### US-502 · Đăng nhập bằng email hoặc Google · P1
- AC1: Đăng nhập Google lần đầu bằng email chưa có Tài khoản thì tạo Tài khoản mới.
- AC2: Đăng nhập Google bằng email đã có Tài khoản email + mật khẩu thì liên kết vào Tài khoản đó **[Giả định]**. Nếu Tài khoản đó chưa xác thực email, mật khẩu cũ bị xoá và mọi phiên đăng nhập cũ mất hiệu lực, để người đã đăng ký trước bằng email của người khác không giữ được quyền truy cập.
- AC3: Đăng nhập sai nhiều lần liên tiếp thì tạm khoá đăng nhập trong một khoảng thời gian.
- AC4: Email thuộc Tài khoản Staff hoặc Admin thì không đăng nhập storefront được, kể cả bằng Google; báo lỗi chung.

### US-503 · Quên mật khẩu · P1
- AC1: Nhập email thì luôn hiện "Nếu email tồn tại, chúng tôi đã gửi hướng dẫn".
- AC2: Link đặt lại mật khẩu dùng một lần và hết hạn sau 1 giờ **[Giả định]**.
- AC3: Đặt lại mật khẩu thành công thì mọi phiên đăng nhập cũ mất hiệu lực.

### US-504 · Sổ địa chỉ · P2
- AC1: Thêm, sửa, xoá địa chỉ; chọn một địa chỉ mặc định.

### US-505 · Chọn ngôn ngữ · P2
- AC1: Chọn vi hoặc en; email sau đó gửi theo ngôn ngữ đã chọn (BR-NTF-02).

---

## E6. Xử lý Đơn hàng (Staff)

### US-601 · Danh sách đơn cần xử lý · P1
- AC1: Lọc theo trạng thái, phương thức thanh toán, khoảng ngày; tìm theo mã đơn hoặc số điện thoại.
- AC2: Lọc được các đơn có Cờ cần xử lý, theo từng loại: phí ship dự phòng (BR-SHP-02), sai số tiền (BR-PAY-04), tiền về cho đơn không còn chờ thanh toán (BR-PAY-05), tạo Vận đơn thất bại (BR-SHP-05). Staff gỡ cờ khi xử lý xong.

### US-602 · Xác nhận và đóng gói · P1
- AC1: Staff chuyển Chờ xác nhận → Đã xác nhận → Đang đóng gói (T6, T8).
- AC2: Chọn nhiều đơn và xác nhận hàng loạt.

### US-603 · Bàn giao vận chuyển · P1
- AC1: Staff bấm bàn giao cho một hoặc nhiều đơn Đang đóng gói; hệ thống tạo Vận đơn ở GHN ở chế độ chạy nền. Khi GHN tạo xong, đơn chuyển sang Đang giao và lưu mã Vận đơn (T10).
- AC2: Tạo Vận đơn thất bại thì đơn giữ nguyên Đang đóng gói, được gắn Cờ cần xử lý và Staff thấy lý do lỗi.
- AC3: Trong lúc Vận đơn đang được tạo, Staff không huỷ được đơn (xem [05-order-lifecycle.md](./05-order-lifecycle.md) mục 4.5).

### US-604 · Staff huỷ đơn · P1
- AC1: Huỷ được ở Chờ xác nhận, Đã xác nhận, Đang đóng gói (T7, T9); bắt buộc nhập lý do.
- AC2: Đơn đã thanh toán online thì tạo yêu cầu Hoàn tiền ở trạng thái chờ xử lý.

### US-605 · Ghi nhận Hoàn tiền thủ công · P1
- AC1: Staff nhập mã giao dịch hoàn và ngày hoàn, yêu cầu chuyển sang Đã hoàn tiền (BR-REF-03); khách nhận email.

### US-606 · Ghi nhận Đổi trả · P1
- AC1: Chỉ tạo được cho đơn Đã giao trong vòng 7 ngày (BR-RET-01).
- AC2: Dòng có Giá khuyến mãi giảm trên 50% không được chọn (BR-RET-03).
- AC3: Khi Staff xác nhận đã nhận và kiểm tra hàng, Tồn kho được cộng lại (BR-INV-08).
- AC4: Đổi trả được chấp nhận thì số tiền Hoàn tiền đề xuất = phần Người mua đã thực trả cho số lượng trả lại (BR-RET-07).

### US-607 · Xử lý đơn Hoàn hàng · P1
- AC1: Đơn Hoàn hàng hiện trong danh sách chờ Staff xác nhận nhận hàng về Kho; xác nhận xong thì cộng lại Tồn kho.

### US-608 · Xử lý tiền về cho đơn không còn chờ thanh toán · P1
- AC1: Có danh sách các yêu cầu Hoàn tiền do hệ thống tự tạo (BR-PAY-05) để Staff xử lý, gồm cả đơn đã huỷ và đơn được trả tiền hai lần.

---

## E7. Tồn kho (Staff)

### US-701 · Nhập kho và điều chỉnh · P1
- AC1: Nhập số lượng nhập kho cho từng Biến thể.
- AC2: Điều chỉnh tăng/giảm bắt buộc chọn lý do; mọi thay đổi được ghi lịch sử (BR-INV-09).

### US-702 · Xem tồn kho · P1
- AC1: Xem theo Biến thể: Tồn kho, số đang Giữ hàng, Số lượng bán được.
- AC2: Lọc các Biến thể có Số lượng bán được dưới một ngưỡng do Staff tự nhập khi lọc (mặc định 5). Ngưỡng này không phải cấu hình hệ thống.

---

## E8. Quản lý Sản phẩm và Danh mục (Admin)

### US-801 · Quản lý Danh mục · P1
- AC1: Tạo Danh mục nhiều cấp, sắp xếp thứ tự hiển thị.

### US-802 · Tạo Sản phẩm và Biến thể · P1
- AC1: Nhập tên, mô tả (tiếng Việt), danh mục, cân nặng (bắt buộc, BR-CAT-06).
- AC2: Chọn danh sách size và màu thì hệ thống sinh ma trận Biến thể; Admin nhập SKU và giá cho từng Biến thể.
- AC3: SKU trùng thì báo lỗi (BR-CAT-03).
- AC4: Upload ảnh theo màu (BR-CAT-05).

### US-803 · Đăng bán và ngừng bán · P1
- AC1: Chuyển Sản phẩm `draft` → `active` → `archived`. Sản phẩm đã có đơn không xoá được (BR-CAT-09).

### US-804 · Đặt Giá khuyến mãi · P1
- AC1: Chọn Biến thể (hoặc toàn bộ Biến thể của một Sản phẩm), nhập giá khuyến mãi và thời gian.
- AC2: Giá khuyến mãi ≥ giá bán thì báo lỗi; trùng thời gian với Giá khuyến mãi khác thì báo lỗi (BR-PRC-01, BR-PRC-02).

---

## E9. Khuyến mãi (Admin)

### US-901 · Tạo Voucher · P1
- AC1: Nhập mã, kiểu giảm (% kèm mức tối đa, hoặc số tiền cố định), giá trị đơn tối thiểu, tổng lượt, lượt mỗi khách, thời gian hiệu lực (BR-VCH-03, BR-VCH-04).
- AC2: Xem được số lượt đã dùng; vô hiệu hoá Voucher bất kỳ lúc nào.

---

## E10. Quản trị hệ thống (Admin)

### US-1001 · Quản lý Tài khoản Staff · P1
- AC1: Tạo, vô hiệu hoá Tài khoản Staff; vô hiệu hoá thì mọi phiên của Tài khoản đó mất hiệu lực ngay.
- AC2: Email đã thuộc một Tài khoản khác (kể cả Tài khoản Khách hàng) thì không tạo được.

### US-1002 · Cấu hình vận hành · P1
- AC1: Sửa được Phí ship dự phòng, ngưỡng miễn phí ship, hạn mức COD; mọi lần sửa được ghi lịch sử.
- AC2: Thời gian Giữ hàng và hạn link thanh toán là cố định, không sửa được (BR-INV-05). Thông tin doanh nghiệp và các chính sách là nội dung tĩnh của Frontend ở MVP (xem [06-compliance.md](./06-compliance.md) mục 4).

### US-1003 · Báo cáo doanh thu cơ bản · P2
- AC1: Doanh thu theo ngày/tháng chỉ tính đơn **Hoàn tất**; có thêm số liệu tạm tính cho đơn Đã giao.
- AC2: Xuất danh sách đơn đã thu tiền theo ngày ra file để kế toán xuất hoá đơn (xem [06-compliance.md](./06-compliance.md)).

---

## E11. Dữ liệu cá nhân

### US-1101 · Yêu cầu xoá dữ liệu · P1
- AC1: Khách hàng gửi yêu cầu xoá trong tài khoản; Khách vãng lai gửi qua kênh hỗ trợ.
- AC2: Staff xử lý yêu cầu thì thông tin cá nhân được ẩn danh, dữ liệu đơn vẫn giữ cho kế toán (CMP-05).
- AC3: Tài khoản đã ẩn danh không đăng nhập được nữa.
- AC4: Yêu cầu chỉ được hoàn thành khi mọi Đơn hàng của người đó đã ở trạng thái cuối (Hoàn tất, Đã huỷ, Hoàn hàng); trước đó yêu cầu ở trạng thái chờ.

### US-1102 · Lịch sử truy cập dữ liệu khách · P2
- AC1: Mỗi lần Staff mở chi tiết thông tin khách được ghi lại: ai, lúc nào, xem khách nào (CMP-07).
