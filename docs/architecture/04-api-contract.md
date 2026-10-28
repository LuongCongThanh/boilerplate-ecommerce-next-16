# 04. API contract

> Trạng thái: **Bản nháp chờ review**. OpenAPI sinh tự động bằng `drf-spectacular` tại `/api/schema/`, Swagger UI tại `/api/docs/` (chỉ bật ở local và staging, không mở ra internet).
>
> Mọi request của storefront và back-office đi qua Next.js BFF ([ADR 0009](../adr/0009-nextjs-bff-django-private.md)). Từ internet chỉ có `/api/v1/webhooks/` gọi thẳng vào Django.

## 1. Quy ước chung

| Chủ đề | Quy ước |
|---|---|
| Gốc URL | `/api/v1/store/` (storefront), `/api/v1/backoffice/` (Staff/Admin), `/api/v1/webhooks/` (VNPay, MoMo, GHN) |
| Phiên bản | Ghi trên URL (`v1`). Thay đổi làm gãy client thì tạo `v2` chạy song song |
| Định dạng | JSON, field `snake_case` tiếng Anh |
| Tiền | `{"amount": 250000, "currency": "VND"}` |
| Thời gian | ISO 8601 có múi giờ, ví dụ `2026-10-25T10:15:00+07:00` |
| ID | UUID. Riêng Đơn hàng dùng `code` trên URL storefront |
| Ngôn ngữ | Header `Accept-Language: vi` (mặc định) hoặc `en`; chỉ ảnh hưởng `error.message` và nhãn hiển thị, không dịch nội dung Sản phẩm |
| Xác thực | `Authorization: Bearer <access_token>` ([05-auth-security.md](./05-auth-security.md)) |
| Giỏ của Khách vãng lai | Header `X-Cart-Token` (Frontend lưu trong cookie `cart_token`) |
| Đơn của Khách vãng lai | Header `X-Lookup-Token`: token 30 phút gắn với đúng một đơn, do `POST checkout` (với Khách vãng lai) hoặc `POST orders/lookup` cấp. Next.js cất token trong session |
| IP người dùng | Django đọc `X-Client-IP` do BFF gửi kèm `X-BFF-Secret` ([05-auth-security.md](./05-auth-security.md) mục 5) |
| Chống tạo trùng | Header `Idempotency-Key` (UUID) **bắt buộc** với `POST /store/checkout`, `POST /store/orders/{code}/payments` và các lệnh ghi Tồn kho cộng dồn ở back-office (`stock/inbound`, `stock/adjust`, `stock/count`). Các endpoint chuyển trạng thái không cần, vì gọi lần hai đã bị máy trạng thái chặn bằng `409 INVALID_TRANSITION`. Key lưu trong PostgreSQL (`shared_idempotency_key`) 24 giờ. Cùng key và cùng body thì trả lại đúng kết quả lần đầu; cùng key nhưng body khác thì `409 IDEMPOTENCY_CONFLICT` |

## 2. Phân trang

```json
GET /api/v1/store/products?page=2&page_size=24
{
  "count": 135,
  "next": "…?page=3&page_size=24",
  "previous": "…?page=1&page_size=24",
  "results": [ … ]
}
```

`page_size` mặc định 24, tối đa 100.

## 3. Định dạng lỗi

Mọi lỗi trả cùng một định dạng (`shared/api/exception_handler.py`):

```json
HTTP 409
{
  "error": {
    "code": "OUT_OF_STOCK",
    "message": "Một số sản phẩm không đủ hàng.",
    "details": {
      "items": [{"sku": "TSHIRT-BASIC-WHT-M", "requested": 3, "available": 1}]
    },
    "request_id": "01JB…"
  }
}
```

| HTTP | Khi nào | Ví dụ `code` |
|---|---|---|
| 400 | Dữ liệu vào sai định dạng | `VALIDATION_ERROR` (kèm `details.fields`) |
| 401 | Chưa đăng nhập, token hết hạn | `NOT_AUTHENTICATED`, `TOKEN_EXPIRED` |
| 403 | Không đủ quyền | `PERMISSION_DENIED` |
| 404 | Không tìm thấy | `NOT_FOUND`, `ORDER_NOT_FOUND` |
| 409 | Xung đột nghiệp vụ | `OUT_OF_STOCK`, `INVALID_TRANSITION`, `IDEMPOTENCY_CONFLICT`, `PRICE_CHANGED`, `SHIPMENT_IN_PROGRESS`, `PAYMENT_WINDOW_CLOSED`, `INSUFFICIENT_AVAILABLE` |
| 422 | Vi phạm quy tắc nghiệp vụ | `VOUCHER_EXPIRED`, `VOUCHER_MIN_ORDER_NOT_MET`, `COD_LIMIT_EXCEEDED`, `LIST_PRICE_BELOW_SALE_PRICE` |
| 429 | Vượt giới hạn tần suất | `THROTTLED` |
| 500 | Lỗi hệ thống | `INTERNAL_ERROR` (không lộ chi tiết) |

Frontend dịch theo `code`; `message` chỉ là bản dịch mặc định theo `Accept-Language`.

Ba mã cần Frontend xử lý riêng:

- `PRICE_CHANGED`: tổng tiền tính lại khi đặt đơn khác `expected_total` (BR-ORD-07). Đơn **không** được tạo; `details.quote` chứa bảng tính mới (Tạm tính, giảm giá Voucher, phí ship, tổng) để Người mua xem lại rồi gửi lại.
- `SHIPMENT_IN_PROGRESS`: Staff huỷ đơn khi Vận đơn đang được tạo ở GHN. Chờ kết quả tạo Vận đơn rồi xử lý tiếp.
- `PAYMENT_WINDOW_CLOSED`: Người mua bắt đầu Thanh toán online từ phút thứ 8 kể từ khi đặt đơn, khi link mới còn quá ít thời gian để trả tiền (BR-INV-05). Đơn sẽ bị huỷ khi Giữ hàng hết hạn; Người mua phải đặt đơn mới.

## 4. Danh sách endpoint

### 4.1. Storefront: `/api/v1/store/`

| Method | Path | Quyền | Mô tả | User story |
|---|---|---|---|---|
| GET | `categories` | Công khai | Cây danh mục | US-101 |
| GET | `products` | Công khai | Danh sách có lọc `category`, `size`, `color` (theo mã trong danh sách size và bảng màu), `price_min`, `price_max`, `in_stock`, `q`, `ordering` (`newest`, `price`, `-price`, `best_selling`) | US-101 → 103 |
| GET | `products/{slug}` | Công khai | Chi tiết, các màu, ảnh, Biến thể kèm giá và còn hàng | US-104 |
| GET | `geo/provinces`, `geo/provinces/{code}/wards` | Công khai | Địa giới 2 cấp | US-301 |
| GET | `cart` | Guest / Customer | Giỏ hàng kèm giá hiện tại và cảnh báo | US-202 |
| POST | `cart/items` | Guest / Customer | Thêm Biến thể | US-201 |
| PATCH | `cart/items/{id}` | Guest / Customer | Đổi số lượng | US-202 |
| DELETE | `cart/items/{id}` | Guest / Customer | Xoá | US-202 |
| POST | `checkout/quote` | Guest / Customer | Tính thử: Tạm tính, Voucher, phí ship, tổng. `total` trả về được gửi lại làm `expected_total` | US-303, 304 |
| POST | `checkout` | Guest / Customer | Đặt đơn (cần `Idempotency-Key`). Body có `payment_method` (`cod \| online`) và `expected_total`; lệch thì `409 PRICE_CHANGED`. Trả `201 {order_code, lookup_token}` (`lookup_token` chỉ có với Khách vãng lai) | US-301 → 307 |
| POST | `orders/{code}/payments` | Customer chủ đơn, hoặc Guest có `X-Lookup-Token` | Bắt đầu một lần Thanh toán online (cần `Idempotency-Key`). Body `{gateway: "vnpay" \| "momo", return_url}`; trả `redirect_url`. Mọi link của đơn hết hạn ở phút thứ 10 kể từ khi đặt đơn (BR-INV-05); từ phút thứ 8 không tạo link mới mà trả `PAYMENT_WINDOW_CLOSED` | US-306 |
| POST | `orders/lookup` | Công khai (throttle chặt) | Khách vãng lai tra cứu bằng `code` + `phone` | US-401 |
| GET | `orders` | Customer | Lịch sử đơn | US-402 |
| GET | `orders/{code}` | Customer chủ đơn, hoặc Guest có `X-Lookup-Token` | Chi tiết đơn | US-402 |
| POST | `orders/{code}/cancel` | Customer chủ đơn, hoặc Guest có `X-Lookup-Token` | Tự huỷ đơn | US-403 |
| POST | `auth/register` | Công khai | Đăng ký | US-501 |
| POST | `auth/verify-email` | Công khai | Xác thực email | US-501 |
| POST | `auth/login` | Công khai | Đăng nhập email + mật khẩu | US-502 |
| POST | `auth/google` | Công khai | Đổi `id_token` Google lấy JWT | US-502 |
| POST | `auth/refresh` | Có refresh token | Lấy access token mới, xoay vòng refresh token | — |
| POST | `auth/logout` | Customer | Thu hồi refresh token | — |
| POST | `auth/password/forgot`, `auth/password/reset` | Công khai | Quên mật khẩu | US-503 |
| GET, PATCH | `me` | Customer | Hồ sơ: họ tên, số điện thoại, ngôn ngữ. Không đổi được email ở MVP | US-505, 506 |
| GET, POST, PATCH, DELETE | `me/addresses` | Customer | Sổ địa chỉ | US-504 |
| POST | `me/erasure-request` | Customer | Yêu cầu xoá dữ liệu | US-1101 |

`checkout` (với Khách vãng lai) và `orders/lookup` trả về một `lookup_token` ngắn hạn (30 phút) gắn với đúng một đơn, để Khách vãng lai thanh toán, xem và huỷ đơn mà không phải nhập lại số điện thoại. Next.js cất token trong session và gửi qua header `X-Lookup-Token`.

### 4.2. Back-office: `/api/v1/backoffice/`

| Method | Path | Quyền | Mô tả |
|---|---|---|---|
| POST | `auth/login`, `auth/refresh`, `auth/logout` | — | Đăng nhập của Staff/Admin (tách khỏi storefront) |
| GET | `orders` | Staff | Lọc theo trạng thái, Phương thức thanh toán, ngày, Cờ cần xử lý (`flag=<kind>`); tìm theo Mã đơn, số điện thoại (tìm theo số điện thoại thì ghi log truy cập, CMP-07) |
| GET | `orders/{id}` | Staff | Chi tiết đơn, lịch sử trạng thái, Cờ cần xử lý (ghi log truy cập, CMP-07) |
| POST | `orders/{id}/flags/{flag_id}/resolve` | Staff | Gỡ Cờ cần xử lý sau khi xử lý xong (ghi lịch sử) |
| POST | `orders/{id}/confirm`, `start-packing`, `cancel` | Staff | Chuyển trạng thái (T6, T8, T7/T9). `cancel` trả `409 SHIPMENT_IN_PROGRESS` khi Vận đơn đang được tạo |
| POST | `orders/{id}/hand-over` | Staff | Bàn giao GHN (T10), chạy nền: trả `202`, đơn sang `SHIPPING` khi GHN tạo Vận đơn xong; lỗi thì gắn cờ `shipment_failed`. Gọi lại sau `shipment_failed` thì dùng lại Vận đơn cũ |
| POST | `orders/bulk/confirm` | Staff | Xác nhận hàng loạt |
| POST | `orders/{id}/returned-to-warehouse` | Staff | Xác nhận đơn Hoàn hàng đã về Kho |
| GET, POST | `refunds`, `refunds/{id}/complete` | Staff | Danh sách Hoàn tiền, ghi nhận đã hoàn |
| GET, POST | `returns`, `returns/{id}/receive`, `accept`, `reject` | Staff | Đổi trả. `accept` nhận `{lines: [{return_line_id, accepted_quantity, restock}]}` (BR-RET-08) |
| GET | `stock` | Staff | Tồn kho, Giữ hàng, Hàng chờ xuất và Số lượng bán được theo Biến thể. Lọc tồn thấp bằng `available_lt=<n>` (mặc định 5, US-702) |
| POST | `stock/inbound`, `stock/adjust` | Staff | Nhập kho, điều chỉnh (bắt buộc lý do, cần `Idempotency-Key`). Giảm quá Số lượng bán được thì `409 INSUFFICIENT_AVAILABLE` (BR-INV-11) |
| POST | `stock/count` | Staff | Kiểm kê (cần `Idempotency-Key`): gửi số đếm theo Biến thể, hệ thống điều chỉnh theo chênh lệch với Tồn kho + Hàng chờ xuất (US-703) |
| GET | `customers`, `customers/{id}` | Staff | Xem khách (ghi log truy cập) |
| GET, POST | `erasure-requests`, `erasure-requests/{id}/complete` | Staff | Xử lý Yêu cầu xoá dữ liệu. `complete` chỉ thành công khi mọi đơn liên quan ở trạng thái cuối và không còn Hoàn tiền chờ xử lý (CMP-05) |
| CRUD | `categories`, `products`, `products/{id}/variants`, `products/{id}/images` | Admin | Quản lý danh mục hàng hoá. Hạ Giá bán xuống ≤ Giá khuyến mãi đang hoặc sắp hiệu lực thì `422 LIST_PRICE_BELOW_SALE_PRICE` (BR-PRC-05) |
| GET, POST, PATCH | `sizes`, `colors` | Admin | Danh sách size và bảng màu; không xoá, chỉ ẩn bằng `is_active = false` (US-805) |
| POST | `products/{id}/publish`, `archive` | Admin | Đăng bán, ngừng bán |
| CRUD | `sale-prices` | Admin | Giá khuyến mãi |
| CRUD | `vouchers` | Admin | Voucher |
| CRUD | `staff` | Admin | Tài khoản Staff |
| GET, PATCH | `settings/ordering` | Admin | Ngưỡng miễn phí ship, hạn mức COD |
| GET, PATCH | `settings/shipping` | Admin | Phí ship dự phòng |
| GET, PATCH | `settings/ghn-locations` | Admin | Ánh xạ phường/xã sang GHN cho các phường/xã chưa có ánh xạ (US-1004) |
| GET | `reports/revenue`, `reports/paid-orders.csv` | Admin | Báo cáo doanh thu, danh sách cho kế toán |

### 4.3. Webhook: `/api/v1/webhooks/`

| Method | Path | Xác thực | Phản hồi |
|---|---|---|---|
| GET | `vnpay/ipn` | Chữ ký HMAC-SHA512 | JSON `{"RspCode": "00", "Message": "Confirm Success"}` theo đặc tả VNPay |
| POST | `momo/ipn` | Chữ ký HMAC-SHA256 | HTTP 204 |
| POST | `ghn` | Token bí mật trong header + IP allow-list **[Cần xác minh cơ chế GHN hỗ trợ]** | HTTP 200 |

Webhook xử lý đồng bộ trong một transaction: kiểm tra chữ ký, lưu dữ liệu gốc, chống trùng, cập nhật Thanh toán hoặc Vận đơn và ghi sự kiện vào outbox. Phần của `ordering` (chuyển trạng thái Đơn hàng) chạy sau qua sự kiện, nên webhook không chờ nó. Mã phản hồi cho từng tình huống theo đặc tả của từng cổng, xem [06-integrations.md](./06-integrations.md). Đây là phần duy nhất của Django mở ra internet.

### 4.4. Vận hành

| Path | Mô tả |
|---|---|
| `/healthz` | Tiến trình còn sống |
| `/readyz` | Kết nối được PostgreSQL. Không kiểm tra Redis, để API vẫn phục vụ khi Redis lỗi ([10-nfr.md](./10-nfr.md) mục 2) |
| `/api/schema/`, `/api/docs/` | OpenAPI và Swagger UI (chỉ local và staging nội bộ, tắt trên production) |
| `/dev/fake-gateway/…` | Trang Fake Gateway (chỉ có khi `FAKE_PROVIDERS_ENABLED = true`, tức local và test) |
