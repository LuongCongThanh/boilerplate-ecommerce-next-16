# Back-office tự xây bằng Next.js thay vì Django Admin

Staff và Admin làm việc trên một app back-office Next.js deploy riêng, gọi tới Django API, thay vì dùng Django Admin đã tuỳ biến. Lý do:

1. Staff cần màn hình theo đúng công việc, ví dụ xử lý đơn hàng loạt và quét mã khi đóng gói.
2. Cần luồng nghiệp vụ có phân quyền, ví dụ ai được huỷ Đơn hàng sau khi đã Đang đóng gói. Kiểu CRUD theo model của Django Admin làm những việc này rất khó.

Đổi lại, phần back-office tốn thêm khoảng 30–40% công sức phát triển.

## Hệ quả

- Django API có một nhánh API riêng cho back-office, mọi thao tác back-office là một endpoint có quy tắc phân quyền riêng.
- Back-office là app riêng nên bundle và bề mặt tấn công không lẫn vào storefront, và có thể giới hạn truy cập theo IP hoặc VPN.
