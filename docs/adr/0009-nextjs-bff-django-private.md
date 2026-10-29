# Next.js là BFF cho mọi request, Django chỉ mở webhook ra internet

Storefront và back-office Next.js là BFF (backend for frontend) cho **mọi** request tới Django, kể cả các endpoint công khai như danh sách Sản phẩm. Next.js chạy trên ECS Fargate cùng VPC với Django. CloudFront đưa trang web vào ALB của Next.js, `/media/*` vào S3, và chỉ `/api/v1/webhooks/*` (VNPay, MoMo, GHN) đi từ internet vào Django. Phần API còn lại của Django không public.

Lý do: [ADR 0002](./0002-auth-nextauth-session-django-jwt.md) đã buộc mọi request có đăng nhập đi qua server Next.js vì trình duyệt không được thấy token. Nếu để endpoint công khai đi thẳng từ trình duyệt còn endpoint có đăng nhập đi qua Next.js, Django sẽ thấy IP thật ở nửa này và IP của server Next.js ở nửa kia, nên throttle theo IP (đăng nhập, tra cứu đơn) không còn đúng, đồng thời phải mở CORS và bề mặt public của Django rộng hơn cần thiết. Chạy Next.js cùng VPC thì dữ liệu cá nhân không đi qua thêm một bên xử lý nào ở nước ngoài ngoài AWS Singapore (CMP-08).

## Các phương án đã cân nhắc

- **Trình duyệt gọi thẳng Django cho endpoint công khai, qua Next.js cho endpoint có đăng nhập**: loại, vì throttle theo IP bị lẫn giữa người dùng thật và server Next.js, và phải bật CORS.
- **Next.js trên Vercel**: loại, vì Django phải mở ra internet để Vercel gọi được, và dữ liệu cá nhân đi qua thêm một bên xử lý ở nước ngoài.

## Hệ quả

- Next.js gửi IP thật của người dùng trong header `X-Client-IP`, kèm `X-BFF-Secret` (biến môi trường `BFF_SHARED_SECRET`). Django chỉ tin `X-Client-IP` khi secret đúng, và throttle theo IP đó. Thiếu hoặc sai secret thì Django dùng IP kết nối như bình thường.
- Không dùng `django-cors-headers`, vì trình duyệt không gọi Django trực tiếp.
- Back-office được giới hạn IP hoặc VPN ở tầng WAF ([ADR 0004](./0004-custom-nextjs-admin.md)).
- Có thêm một service phải deploy và theo dõi trên ECS. Swagger UI và OpenAPI chỉ truy cập được từ mạng nội bộ.
- Khi có client khác (ví dụ mobile app), phải quyết định lại: hoặc đi qua một BFF riêng, hoặc mở một nhánh API public có throttle và xác thực riêng.
