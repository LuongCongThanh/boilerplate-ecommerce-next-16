# Frontend Next.js tách riêng, Backend là Django API

Storefront là một ứng dụng Next.js gọi tới một Django API riêng, thay vì một Django monolith render template. Lý do: tái sử dụng thiết kế và tài liệu Next.js đã có, có SSR/SEO và tương tác phong phú cho storefront, đồng thời giữ toàn bộ quy tắc nghiệp vụ ở một backend Django duy nhất mà các client sau này (ví dụ mobile app) cũng gọi được.

## Hệ quả

- Có hai thứ phải deploy, hai ngôn ngữ (TypeScript và Python) và một API contract tường minh phải được version hoá và giữ đồng bộ.
- Xác thực trải trên cả hai phía: Next.js giữ session, Django phát hành và kiểm tra token (xem [0002](./0002-auth-nextauth-session-django-jwt.md)).
