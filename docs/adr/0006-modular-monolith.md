# Modular monolith: mỗi module nghiệp vụ là một Django app

Backend Fashion Store là một Django project duy nhất, dùng chung PostgreSQL, deploy cùng một phiên bản. Mỗi module nghiệp vụ là một Django app riêng trong package `modules` (`modules.catalog`, `modules.ordering`…); `modules` chỉ là package nhóm, không đăng ký thành app. Hạ tầng dùng chung (outbox sự kiện, dữ liệu địa giới hành chính) nằm trong app `shared`; app này không chứa nghiệp vụ và không import `modules`.

Quyết định được chốt ngày 27/10/2026, thay lựa chọn một app nghiệp vụ trong bản nháp trước khi khởi tạo Backend. Chọn app riêng để Django quản lý migrations, model và cơ chế discovery theo từng module, thay vì tự duy trì các điểm nạp tập trung. Các app vẫn chạy trong cùng project và dùng chung transaction database.

Ranh giới giữa các module được giữ bằng ba quy tắc:

1. Module chỉ gọi nhau qua `contracts.py` của module kia; được import thêm `events.py` và `exceptions.py` của module lớp dưới. Ngoại lệ import model để khai báo FK được mô tả bên dưới. `import-linter` kiểm tra quy tắc này trong CI.
2. Việc phụ, và mọi thông báo từ lớp dưới lên lớp trên, đi qua sự kiện phát sau khi transaction commit.
3. Phụ thuộc chỉ đi một chiều, từ trên xuống:
   `notifications` → `ordering` → `inventory`, `promotions` → `identity`, `catalog`, `payments`, `shipping` → `shared`.
   Các module cùng lớp không import lẫn nhau.

Khoá ngoại (FK) giữa các module được phép, nhưng chỉ theo chiều phụ thuộc ở quy tắc 3.

`payments` và `shipping` được đặt ở lớp dưới `ordering` và không biết gì về Đơn hàng. Chúng chỉ làm việc với một mã tham chiếu (`reference`) và báo kết quả lên bằng sự kiện. Nhờ vậy `ordering` gọi được chúng khi checkout mà không tạo vòng phụ thuộc. Giá khuyến mãi nằm trong `catalog` cùng với giá bán, vì danh sách Sản phẩm cần lọc và sắp xếp theo giá áp dụng.

Mỗi app có `AppConfig` riêng, `name` là đường dẫn đầy đủ (ví dụ `modules.identity`), `label` là tên module (`identity`). Đăng ký từng config trong `INSTALLED_APPS`; `AUTH_USER_MODEL = "identity.Account"`.

## Các phương án đã cân nhắc

- **Một Django app nghiệp vụ `modules`**: ít mục đăng ký hơn nhưng gom migrations và namespace model, đồng thời cần các điểm nạp tập trung. Không chọn vì lợi ích giảm cấu hình không bù được chi phí quản lý này.
- **Cấm FK giữa các module, chỉ lưu ID**: không chọn, vì mất ràng buộc toàn vẹn ở database đối với dữ liệu tiền và hàng.

## Hệ quả

- Mỗi app có `migrations/` riêng; migration có FK sang app khác khai báo dependency tương ứng. Xung đột migration trong cùng app vẫn cần xử lý; số migration giống nhau ở hai app khác nhau là hợp lệ.
- `models/__init__.py` của từng app export các model của app đó để Django nhận ra. `admin.py`, `management/commands/` và `templates/` nằm trong app sở hữu; không có `modules/models.py` hay `modules/admin.py` tập trung.
- Mỗi model khai báo `Meta.db_table` có tiền tố theo module (ví dụ `catalog_product`). Tên class model chỉ cần duy nhất trong app; định danh Django dùng `app_label.ModelName`, ví dụ `identity.Account`.
- `AppConfig.ready()` của từng app nạp handler của chính app nếu có, không truy vấn DB khi khởi động. Celery autodiscover task của các app đã đăng ký; task lồng sâu như `shared.events.tasks` phải được nạp tường minh.
- App riêng không tự ngăn import hay truy vấn xuyên module, không tạo database riêng và không phải microservice.
- Ranh giới giữa các module chỉ được kiểm tra ở mức import trong code, nên `import-linter` là bắt buộc trong CI, không phải tuỳ chọn.
- FK sang module khác khai báo bằng class được import, kể cả FK tới `Account`, không khai báo bằng chuỗi (`settings.AUTH_USER_MODEL`, `"catalog.Variant"`). FK khai báo bằng chuỗi không tạo import nên `import-linter` không kiểm tra được chiều của nó.
- FK chỉ để database giữ toàn vẹn dữ liệu, không để truy vấn xuyên module: không dùng lookup `__`, `select_related`, `prefetch_related` đi vào model của module khác, mà lấy dữ liệu qua `contracts.py`. Nếu không, schema của module kia sẽ ngầm thành một phần interface của nó. ORM đi qua FK mà không cần import, nên quy tắc này chỉ kiểm tra được khi review.
- Dòng đơn hàng lưu bản chụp (snapshot) tên, SKU và đơn giá tại thời điểm đặt, nên vẫn đúng dù Sản phẩm thay đổi sau này.
