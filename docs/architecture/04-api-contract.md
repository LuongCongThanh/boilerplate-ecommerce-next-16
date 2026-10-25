# 04. API contract

> Trạng thái: **Bản nháp chờ review**. OpenAPI sinh tự động bằng `drf-spectacular` tại `/api/schema/`, Swagger UI tại `/api/docs/` (chỉ bật ở local và staging).

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
| Chống tạo trùng | Header `Idempotency-Key` (UUID) **bắt buộc** với `POST /store/checkout` và `POST /store/orders/{code}/payments`. Cùng key trong 24 giờ thì trả lại đúng kết quả lần đầu |

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
| 409 | Xung đột nghiệp vụ | `OUT_OF_STOCK`, `INVALID_TRANSITION`, `IDEMPOTENCY_CONFLICT` |
| 422 | Vi phạm quy tắc nghiệp vụ | `VOUCHER_EXPIRED`, `VOUCHER_MIN_ORDER_NOT_MET`, `COD_LIMIT_EXCEEDED` |
| 429 | Vượt giới hạn tần suất | `THROTTLED` |
| 500 | Lỗi hệ thống | `INTERNAL_ERROR` (không lộ chi tiết) |

Frontend dịch theo `code`; `message` chỉ là bản dịch mặc định theo `Accept-Language`.

## 4. Danh sách endpoint

### 4.1. Storefront: `/api/v1/store/`

| Method | Path | Quyền | Mô tả | User story |
|---|---|---|---|---|
| GET | `categories` | Công khai | Cây danh mục | US-101 |
| GET | `products` | Công khai | Danh sách có lọc `category`, `size`, `color`, `price_min`, `price_max`, `in_stock`, `q`, `ordering` | US-101 → 103 |
| GET | `products/{slug}` | Công khai | Chi tiết, các màu, ảnh, Biến thể kèm giá và còn hàng | US-104 |
| GET | `geo/provinces`, `geo/provinces/{code}/wards` | Công khai | Địa giới 2 cấp | US-301 |
| GET | `cart` | Guest / Customer | Giỏ hàng kèm giá hiện tại và cảnh báo | US-202 |
| POST | `cart/items` | Guest / Customer | Thêm Biến thể | US-201 |
| PATCH | `cart/items/{id}` | Guest / Customer | Đổi số lượng | US-202 |
| DELETE | `cart/items/{id}` | Guest / Customer | Xoá | US-202 |
| POST | `checkout/quote` | Guest / Customer | Tính thử: tạm tính, Voucher, phí ship, tổng | US-303, 304 |
| POST | `checkout` | Guest / Customer | Đặt đơn (cần `Idempotency-Key`) | US-301 → 307 |
| POST | `orders/{code}/payments` | Guest / Customer | Bắt đầu thanh toán VNPay / MoMo, trả `redirect_url` | US-306 |
| POST | `orders/lookup` | Công khai (throttle chặt) | Khách vãng lai tra cứu bằng `code` + `phone` | US-401 |
| GET | `orders` | Customer | Lịch sử đơn | US-402 |
| GET | `orders/{code}` | Customer chủ đơn, hoặc Guest có `lookup_token` | Chi tiết đơn | US-402 |
| POST | `orders/{code}/cancel` | Customer chủ đơn, hoặc Guest có `lookup_token` | Tự huỷ đơn | US-403 |
| POST | `auth/register` | Công khai | Đăng ký | US-501 |
| POST | `auth/verify-email` | Công khai | Xác thực email | US-501 |
| POST | `auth/login` | Công khai | Đăng nhập email + mật khẩu | US-502 |
| POST | `auth/google` | Công khai | Đổi `id_token` Google lấy JWT | US-502 |
| POST | `auth/refresh` | Có refresh token | Lấy access token mới, xoay vòng refresh token | — |
| POST | `auth/logout` | Customer | Thu hồi refresh token | — |
| POST | `auth/password/forgot`, `auth/password/reset` | Công khai | Quên mật khẩu | US-503 |
| GET, PATCH | `me` | Customer | Hồ sơ, ngôn ngữ | US-505 |
| GET, POST, PATCH, DELETE | `me/addresses` | Customer | Sổ địa chỉ | US-504 |
| POST | `me/erasure-request` | Customer | Yêu cầu xoá dữ liệu | US-1101 |

`orders/lookup` trả về một `lookup_token` ngắn hạn (30 phút) để Khách vãng lai xem và huỷ đơn mà không phải nhập lại số điện thoại.

### 4.2. Back-office: `/api/v1/backoffice/`

| Method | Path | Quyền | Mô tả |
|---|---|---|---|
| POST | `auth/login`, `auth/refresh`, `auth/logout` | — | Đăng nhập của Staff/Admin (tách khỏi storefront) |
| GET | `orders` | Staff | Lọc theo trạng thái, phương thức, ngày; tìm theo mã, số điện thoại |
| GET | `orders/{id}` | Staff | Chi tiết đơn, lịch sử trạng thái |
| POST | `orders/{id}/confirm`, `start-packing`, `hand-over`, `cancel` | Staff | Chuyển trạng thái (T6, T8, T10, T7/T9) |
| POST | `orders/bulk/confirm` | Staff | Xác nhận hàng loạt |
| POST | `orders/{id}/returned-to-warehouse` | Staff | Xác nhận đơn Hoàn hàng đã về Kho |
| GET, POST | `refunds`, `refunds/{id}/complete` | Staff | Danh sách Hoàn tiền, ghi nhận đã hoàn |
| GET, POST | `returns`, `returns/{id}/receive`, `accept`, `reject` | Staff | Đổi trả |
| GET | `stock` | Staff | Tồn kho theo Biến thể |
| POST | `stock/inbound`, `stock/adjust` | Staff | Nhập kho, điều chỉnh (bắt buộc lý do) |
| GET | `customers`, `customers/{id}` | Staff | Xem khách (ghi log truy cập) |
| GET, POST | `erasure-requests`, `erasure-requests/{id}/complete` | Staff | Xử lý yêu cầu xoá dữ liệu |
| CRUD | `categories`, `products`, `products/{id}/variants`, `products/{id}/images` | Admin | Quản lý danh mục hàng hoá |
| POST | `products/{id}/publish`, `archive` | Admin | Đăng bán, ngừng bán |
| CRUD | `sale-prices` | Admin | Giá khuyến mãi |
| CRUD | `vouchers` | Admin | Voucher |
| CRUD | `staff` | Admin | Tài khoản Staff |
| GET, PATCH | `settings` | Admin | Cấu hình vận hành |
| GET | `reports/revenue`, `reports/paid-orders.csv` | Admin | Báo cáo doanh thu, danh sách cho kế toán |

### 4.3. Webhook: `/api/v1/webhooks/`

| Method | Path | Xác thực | Phản hồi |
|---|---|---|---|
| GET | `vnpay/ipn` | Chữ ký HMAC-SHA512 | JSON `{"RspCode": "00", "Message": "Confirm Success"}` theo đặc tả VNPay |
| POST | `momo/ipn` | Chữ ký HMAC-SHA256 | HTTP 204 |
| POST | `ghn` | Token bí mật trong header + IP allow-list **[Cần xác minh cơ chế GHN hỗ trợ]** | HTTP 200 |

Webhook luôn trả thành công nhanh sau khi lưu dữ liệu gốc và chống trùng; việc xử lý nghiệp vụ chạy qua sự kiện.

### 4.4. Vận hành

| Path | Mô tả |
|---|---|
| `/healthz` | Tiến trình còn sống |
| `/readyz` | Kết nối được PostgreSQL và Redis |
| `/api/schema/`, `/api/docs/` | OpenAPI và Swagger UI (tắt trên production) |
| `/dev/fake-gateway/…` | Trang Fake Gateway (chỉ có ở local) |
