# Khoá chính UUID v7, sinh qua hàm bọc `shared.models.uuid7`

Mọi bảng dùng khoá chính UUID v7. `default` của `id` trong `shared.models.BaseModel` là hàm của chính repo, `shared.models.uuid7()`; hàm này gọi `uuid_utils.compat.uuid7` (bản `compat` trả `uuid.UUID` chuẩn mà `UUIDField` của Django nhận được). UUID không lộ số lượng đơn hay khách qua ID tăng dần; v7 có tiền tố thời gian nên sắp xếp được theo thời gian tạo và không làm index B-tree phân mảnh như v4. Python 3.13 chưa có `uuid.uuid7()` (có từ 3.14) nên tạm dùng package ngoài.

Django ghi đường dẫn của `default` vào mọi file migration. Nếu trỏ thẳng vào `uuid_utils.compat.uuid7`, gỡ `uuid-utils` sẽ làm migration cũ lỗi khi import. Hàm bọc giữ đường dẫn trong migration cố định là `shared.models.uuid7`, nên chỉ cần sửa thân hàm. Hàm bọc phải có trước migration đầu tiên; sau đó muốn đổi thì phải sửa hoặc squash các migration đã có.

## Các phương án đã cân nhắc

- **Số tự tăng (`BigAutoField`)**: loại, vì lộ quy mô kinh doanh qua ID trong URL và API.
- **UUID v4 (`uuid.uuid4`, có sẵn)**: loại, vì ngẫu nhiên hoàn toàn nên chèn rải rác khắp index và không sắp xếp được theo thời gian.

## Hệ quả

- Khi nâng lên Python 3.14, sửa thân `shared.models.uuid7()` thành `uuid.uuid7()` và bỏ `uuid-utils`. Giá trị đã lưu và các file migration không cần đổi.
- Đổi kiểu cột (ví dụ sang số tự tăng) mới là việc tốn kém, vì phải migrate mọi bảng và mọi FK. Đổi cách sinh UUID (v7 sang v4) thì chỉ cần sửa hàm bọc.
- 48 bit đầu của UUID v7 là thời điểm tạo, tính bằng mili giây. Ai có `id` của Khách hàng, Địa chỉ hay Sản phẩm qua API đều biết bản ghi đó được tạo lúc nào. Rủi ro này được chấp nhận. Đơn hàng dùng `code` trên URL storefront nên không bị ảnh hưởng.
- Mã đơn (`ordering_order.code`) theo cùng lý do: không đánh số tuần tự mà là `FS<YYMM>-` cộng 6 ký tự Crockford Base32 ngẫu nhiên (ví dụ `FS2610-7K3QZD`), có ràng buộc `UNIQUE` và sinh lại khi trùng. Mã tuần tự theo tháng sẽ lộ số Đơn hàng mỗi tháng và dễ đoán, khiến việc tra cứu đơn của Khách vãng lai (Mã đơn + số điện thoại) chỉ còn dựa vào việc đoán số điện thoại.
