# NextAuth giữ session trên trình duyệt, Django tự phát hành JWT bằng PyJWT

Django là nguồn sự thật duy nhất về danh tính và phát hành cặp access/refresh JWT thông qua một module mỏng tự viết trên nền PyJWT. Các app Next.js (storefront và back-office) chỉ dùng NextAuth v4 để cất token trong session cookie httpOnly đã mã hoá và refresh token, không bao giờ dùng NextAuth làm nơi lưu danh tính. Lý do: mọi client, kể cả mobile app sau này, đều xác thực qua cùng một Django API, còn JavaScript trên trình duyệt không bao giờ thấy token thô.

## Các phương án đã cân nhắc

- **djangorestframework-simplejwt**: không chọn, vì tổ chức Jazzband đang giải thể (archive đầu 2027) và chưa rõ package sẽ chuyển về đâu.
- **django-ninja-jwt**: còn được duy trì nhưng metadata đã cũ. Phần JWT cần có đủ nhỏ để tự sở hữu toàn bộ.

## Hệ quả

- Phần mật mã do PyJWT đảm nhiệm, không tự viết. Module tự viết chỉ lo vòng đời token: xoay vòng refresh token, phát hiện refresh token bị dùng lại, và thu hồi token qua `jti`. Module này phải có test bám theo OWASP JWT Cheat Sheet.
- Logic refresh token nằm trong callback `jwt` của NextAuth; Django phải có endpoint refresh và logout.
- Đăng nhập Google được Django xác minh (dùng `google-auth`) chứ không phải NextAuth, để quy tắc liên kết tài khoản chỉ nằm ở một chỗ.
