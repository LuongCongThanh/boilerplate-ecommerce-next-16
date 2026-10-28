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
| Chống tạo trùng | Header Idempotency-Key (UUID) bắt buộc với checkout, bắt đầu Thanh toán và các lệnh ghi Tồn kho cộng dồn ở back-office (`stock/inbound`, `stock/adjust`, `stock/count`, scope là endpoint + `account_id` của Staff). Các endpoint chuyển trạng thái không cần, vì gọi lần hai đã bị máy trạng thái chặn bằng `409 INVALID_TRANSITION`. Key lưu PostgreSQL theo endpoint + Người mua, có in_progress/completed và resource_id. Cùng key khác body trả 409 IDEMPOTENCY_CONFLICT; còn xử lý trả 202 với Retry-After; hoàn tất trả kết quả đã lưu. Giữ completed 24 giờ; không purge in_progress chưa rõ kết quả. Xác nhận quote mới hoặc bắt đầu lần thử khác phải dùng key mới. Frontend sinh key mới mỗi khi body đổi, ví dụ sau `PRICE_CHANGED` |

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
| 409 | Xung đột với trạng thái hiện tại của hệ thống | `OUT_OF_STOCK`, `INVALID_TRANSITION`, `REFRESH_SUPERSEDED`, `IDEMPOTENCY_CONFLICT`, `PRICE_CHANGED`, `SHIPMENT_IN_PROGRESS`, `PAYMENT_WINDOW_CLOSED`, `INSUFFICIENT_AVAILABLE` |
| 422 | Yêu cầu không thoả quy tắc nghiệp vụ | `VOUCHER_NOT_FOUND`, `VOUCHER_EXPIRED`, `VOUCHER_USAGE_LIMIT_REACHED`, `VOUCHER_BUYER_LIMIT_REACHED`, `VOUCHER_MIN_ORDER_NOT_MET`, `COD_LIMIT_EXCEEDED`, `LIST_PRICE_BELOW_SALE_PRICE` |
| 429 | Vượt giới hạn tần suất | `THROTTLED` |
| 500 | Lỗi hệ thống | `INTERNAL_ERROR` (không lộ chi tiết) |

Chọn 409 hay 422 cho mã mới:

- **409**: kết quả phụ thuộc trạng thái hệ thống, và trạng thái đó có thể đã đổi từ lúc client xem (Tồn kho, trạng thái đơn, giá, idempotency). Client nên tải lại dữ liệu rồi thử lại.
- **422**: chính yêu cầu không thoả quy tắc (Voucher không áp được cho đơn này, vượt Hạn mức COD, giá không hợp lệ). Gửi lại y nguyên vẫn lỗi.

Các mã Voucher là lớp con của `VoucherNotApplicable` trong `promotions`, mỗi lý do một mã để Frontend báo đúng lý do (US-304 AC2).

Frontend dịch theo `code`; `message` chỉ là bản dịch mặc định theo `Accept-Language`.

Ba mã cần Frontend xử lý riêng:

- `PRICE_CHANGED`: tổng tiền khác expected_total, hoặc phiên bản giá/dữ liệu snapshot/điều kiện bán thay đổi khi kiểm tra lại trong transaction, kể cả tổng tiền không đổi (BR-ORD-07). Rollback trước khi lấy lại quote ngoài transaction; đơn không được tạo. details.quote chứa bảng tính mới và chỉ rõ dòng không còn bán được; không bịa giá cho dòng đã bị ẩn. Client xác nhận bằng key mới.
- `PAYMENT_INITIALIZING` (202): giao dịch đang tạo/chưa rõ kết quả. Response `{payment_id, code: "PAYMENT_INITIALIZING"}` kèm Retry-After; thử lại cùng endpoint/body/key. Nếu đã thanh toán/hết hạn mà không còn link, kết quả cuối trả payment_id/status để xem lại Đơn hàng; không tạo/gia hạn link mới.
- `SHIPMENT_IN_PROGRESS`: Staff huỷ đơn khi Vận đơn đang được tạo ở GHN. Chờ kết quả tạo Vận đơn rồi xử lý tiếp.
- `PAYMENT_WINDOW_CLOSED`: Người mua bắt đầu Thanh toán online từ phút thứ 8 kể từ khi đặt đơn, khi link mới còn quá ít thời gian để trả tiền (BR-INV-05). Đơn sẽ bị huỷ khi Giữ hàng hết hạn; Người mua phải đặt đơn mới.

## 4. Danh sách endpoint

### 4.1. Storefront: `/api/v1/store/`

| Method | Path | Module | Quyền | Mô tả | User story |
|---|---|---|---|---|---|
| GET | `categories` | catalog | Công khai | Cây danh mục | US-101 |
| GET | `products` | catalog | Công khai | Danh sách có lọc `category`, `size`, `color` (theo mã trong danh sách size và bảng màu), `price_min`, `price_max`, `in_stock`, `q`, `ordering` (`newest`, `price`, `-price`, `best_selling`) | US-101 → 103 |
| GET | `products/{slug}` | catalog | Công khai | Chi tiết, các màu, ảnh, Biến thể kèm giá và còn hàng | US-104 |
| GET | `geo/provinces` | shared | Công khai | Danh sách tỉnh/thành | US-301 |
| GET | `geo/provinces/{code}/wards` | shared | Công khai | Phường/xã của một tỉnh/thành | US-301 |
| GET | `cart` | ordering | Guest / Customer | Giỏ hàng kèm giá hiện tại và cảnh báo | US-202 |
| POST | `cart/items` | ordering | Guest / Customer | Thêm Biến thể. Khách vãng lai chưa có giỏ (không gửi `X-Cart-Token`) thì tạo giỏ mới và trả `cart_token` | US-201 |
| PATCH | `cart/items/{id}` | ordering | Guest / Customer | Đổi số lượng | US-202 |
| DELETE | `cart/items/{id}` | ordering | Guest / Customer | Xoá | US-202 |
| POST | `cart/merge` | ordering | Customer, kèm `X-Cart-Token` | Gộp giỏ vãng lai vào giỏ của Tài khoản (BR-CRT-03). Next.js gọi ngay sau khi đăng nhập thành công | US-204 |
| POST | `checkout/quote` | ordering | Guest / Customer | Tính thử: Tạm tính, Voucher, Phí ship, Tổng tiền đơn. `total` trả về được gửi lại làm `expected_total` | US-303, 304 |
| POST | `checkout` | ordering | Guest / Customer | Đặt đơn (cần `Idempotency-Key`). Body có `payment_method` (`cod \| online`) và `expected_total`; lệch thì `409 PRICE_CHANGED`. Trả `201 {order_code, lookup_token}` (`lookup_token` chỉ có với Khách vãng lai) | US-301 → 307 |
| POST | `orders/{code}/payments` | ordering | Customer chủ đơn, hoặc Guest có `X-Lookup-Token` | Bắt đầu một lần Thanh toán online (cần `Idempotency-Key`), gọi `payments.contracts.start_payment`. Body `{gateway: "vnpay" \| "momo"}`; backend tự dựng URL quay về, gửi `return_url` bị từ chối `400 INVALID_RETURN_URL`. Sẵn sàng thì trả `redirect_url`, chưa xong thì `202 PAYMENT_INITIALIZING`. Mọi link của đơn hết hạn ở phút thứ 10 kể từ khi đặt đơn (BR-INV-05); từ phút thứ 8 không tạo link mới mà trả `PAYMENT_WINDOW_CLOSED`. Gọi lại cùng key thì tiếp tục hoặc trả kết quả của Payment cũ ([06](./06-integrations.md) mục 3.1) | US-306 |
| POST | `orders/lookup` | ordering | Công khai (throttle chặt) | Khách vãng lai tra cứu bằng `code` + `phone`, nhận `lookup_token` | US-401 |
| GET | `orders` | ordering | Customer | Lịch sử đơn | US-402 |
| GET | `orders/{code}` | ordering | Customer chủ đơn, hoặc Guest có `X-Lookup-Token` | Chi tiết đơn | US-402 |
| POST | `orders/{code}/cancel` | ordering | Customer chủ đơn, hoặc Guest có `X-Lookup-Token` | Tự huỷ đơn | US-403 |
| POST | `auth/register` | identity | Công khai | Đăng ký | US-501 |
| POST | `auth/verify-email` | identity | Công khai | Xác thực email bằng token trong link | US-501 |
| POST | `auth/verify-email/resend` | identity | Công khai (throttle) | Gửi lại email xác thực; luôn trả `202` như nhau dù email có tồn tại hay không | US-501 |
| POST | `auth/login` | identity | Công khai | Đăng nhập email + mật khẩu | US-502 |
| POST | `auth/google` | identity | Công khai | Đổi `id_token` Google lấy JWT | US-502 |
| POST | `auth/refresh` | identity | Có refresh token | Xoay refresh token: request trùng trong 10 giây trả chính cặp đã cấp, không tạo nhánh; successor đã dùng thì `409 REFRESH_SUPERSEDED` ([05](./05-auth-security.md) mục 2.1) | — |
| POST | `auth/logout` | identity | Customer | Thu hồi refresh token | — |
| POST | `auth/password/forgot` | identity | Công khai | Gửi link đặt lại mật khẩu; luôn trả `202` như nhau | US-503 |
| POST | `auth/password/reset` | identity | Công khai | Đặt lại mật khẩu bằng token trong link | US-503 |
| GET | `me` | identity | Customer | Hồ sơ | US-505, 506 |
| PATCH | `me` | identity | Customer | Sửa họ tên, số điện thoại, ngôn ngữ, và lựa chọn nhận email marketing (`marketing_opt_in`, mỗi lần đổi ghi một Consent mới, CMP-03). Không đổi được email ở MVP | US-505, 506 |
| GET | `me/addresses` | identity | Customer | Sổ địa chỉ | US-504 |
| POST | `me/addresses` | identity | Customer | Thêm địa chỉ | US-504 |
| PATCH | `me/addresses/{id}` | identity | Customer | Sửa địa chỉ, đặt làm mặc định | US-504 |
| DELETE | `me/addresses/{id}` | identity | Customer | Xoá địa chỉ | US-504 |
| POST | `me/erasure-request` | identity | Customer | Gửi Yêu cầu xoá dữ liệu | US-1101 |

`checkout` (với Khách vãng lai) và `orders/lookup` trả về một `lookup_token` gắn với đúng một đơn, để Khách vãng lai thanh toán, xem và huỷ đơn mà không phải nhập lại số điện thoại. Token được ký bằng `django.core.signing.TimestampSigner`, chỉ mang Mã đơn và hết hạn sau 30 phút. Django không lưu token mà kiểm tra chữ ký trong `IsOrderOwner`, nên token không thu hồi sớm được; với thời hạn 30 phút thì chấp nhận được. Next.js cất token trong session và gửi qua header `X-Lookup-Token`.

Gộp giỏ là endpoint riêng của `ordering` thay vì nằm trong `auth/login`, vì `identity` ở lớp dưới không được gọi `ordering` ([02-backend-structure.md](./02-backend-structure.md) mục 4).

### 4.2. Back-office: `/api/v1/backoffice/`

| Method | Path | Module | Quyền | Mô tả |
|---|---|---|---|---|
| POST | `auth/login` | identity | Công khai | Đăng nhập của Staff/Admin (tách khỏi storefront) |
| POST | `auth/refresh` | identity | Có refresh token | Lấy access token mới, xoay vòng refresh token |
| POST | `auth/logout` | identity | Staff | Thu hồi refresh token |
| POST | `auth/password/forgot` | identity | Công khai | Staff/Admin quên mật khẩu, cùng cơ chế với storefront (05 mục 3) |
| POST | `auth/password/reset` | identity | Công khai | Đặt lại mật khẩu bằng token trong link |
| GET | `orders` | ordering | Staff | Lọc theo trạng thái, Phương thức thanh toán, ngày, Cờ cần xử lý (`flag=<kind>`), Khách hàng (`customer_id`); tìm theo Mã đơn, số điện thoại (tìm theo số điện thoại thì ghi log truy cập, CMP-07) |
| GET | `orders/{id}` | ordering | Staff | Chi tiết đơn, lịch sử trạng thái, Cờ cần xử lý (ghi log truy cập, CMP-07) |
| POST | `orders/{id}/flags/{flag_id}/resolve` | ordering | Staff | Gỡ Cờ cần xử lý sau khi xử lý xong (ghi lịch sử) |
| POST | `orders/{id}/confirm` | ordering | Staff | Xác nhận đơn (T6) |
| POST | `orders/{id}/start-packing` | ordering | Staff | Bắt đầu đóng gói (T8) |
| POST | `orders/{id}/cancel` | ordering | Staff | Huỷ đơn (T7, T9, T14), bắt buộc lý do. Trả `409 SHIPMENT_IN_PROGRESS` khi Vận đơn `requested` hoặc `creation_unknown`; đơn `SHIPPING` chỉ huỷ được khi Vận đơn gặp sự cố (T14) |
| POST | `orders/{id}/hand-over` | ordering | Staff | Bàn giao GHN (T10), chạy nền: trả `202`, đơn sang `SHIPPING` khi GHN tạo Vận đơn xong; lỗi thì gắn cờ `shipment_failed`. Chỉ dùng lại Vận đơn cũ sau `shipment_failed` đã xác nhận chưa tạo bên GHN; `creation_unknown` phải đối soát trước |
| POST | `orders/bulk/confirm` | ordering | Staff | Xác nhận hàng loạt (US-602) |
| POST | `orders/bulk/hand-over` | ordering | Staff | Bàn giao hàng loạt (US-603) |
| POST | `orders/{id}/returned-to-warehouse` | ordering | Staff | Xác nhận hàng đã về Kho, cho đơn Hoàn hàng hoặc đơn huỷ theo T14 khi hàng chưa rời Kho |
| GET | `returns` | ordering | Staff | Danh sách Đổi trả |
| POST | `returns` | ordering | Staff | Ghi nhận yêu cầu Đổi trả cho một đơn Đã giao (US-606) |
| POST | `returns/{id}/receive` | ordering | Staff | Xác nhận đã nhận hàng gửi trả; Tồn kho chưa được cộng lại |
| POST | `returns/{id}/accept` | ordering | Staff | Chấp nhận theo từng dòng, body `{lines: [{return_line_id, accepted_quantity, restock}]}` (BR-RET-08); tạo yêu cầu Hoàn tiền |
| POST | `returns/{id}/reject` | ordering | Staff | Từ chối, kèm ghi chú việc gửi lại hàng (BR-RET-09) |
| GET | `refunds` | payments | Staff | Danh sách Hoàn tiền kèm `payment_id`, gateway và số tiền, lọc theo trạng thái |
| POST | `refunds/{id}/complete` | payments | Staff | Ghi nhận đã hoàn: mã giao dịch hoàn, ngày hoàn (BR-REF-03). Gọi lại cùng dữ liệu trả kết quả cũ, không phát thêm sự kiện; khác dữ liệu đã ghi thì từ chối |
| GET | `stock` | inventory | Staff | Tồn kho, Giữ hàng, Hàng chờ xuất và Số lượng bán được theo Biến thể; SKU và tên lấy qua `catalog.contracts`. Lọc tồn thấp bằng `available_lt=<n>` (mặc định 5, US-702) |
| POST | `stock/inbound` | inventory | Staff | Nhập kho (cần `Idempotency-Key`) |
| POST | `stock/adjust` | inventory | Staff | Điều chỉnh, bắt buộc lý do, cần `Idempotency-Key`. Giảm quá Số lượng bán được thì `409 INSUFFICIENT_AVAILABLE` (BR-INV-11) |
| POST | `stock/count` | inventory | Staff | Kiểm kê (cần `Idempotency-Key`): gửi số đếm theo Biến thể, hệ thống điều chỉnh theo chênh lệch với Tồn kho + Hàng chờ xuất (US-703) |
| GET | `customers` | identity | Staff | Danh sách Khách hàng |
| GET | `customers/{id}` | identity | Staff | Chi tiết Khách hàng (ghi log truy cập, CMP-07). Lịch sử đơn lấy bằng `GET orders?customer_id=` |
| GET | `erasure-requests` | ordering | Staff | Danh sách Yêu cầu xoá dữ liệu (đọc qua `identity.contracts`) |
| POST | `erasure-requests` | ordering | Staff | Tạo yêu cầu cho Khách vãng lai sau khi xác minh qua kênh hỗ trợ |
| POST | `erasure-requests/{id}/complete` | ordering | Staff | Kiểm tra mọi đơn liên quan ở trạng thái cuối và không còn Hoàn tiền chờ xử lý (CMP-05), chuyển yêu cầu sang `processing` rồi trả `202` kèm `request_id` và `status`. Gọi lại không phát thêm sự kiện; đã `completed` thì trả kết quả hiện tại. `completed_at` chỉ có khi mọi bước ẩn danh bắt buộc thành công |
| GET | `categories` | catalog | Admin | Cây danh mục |
| POST | `categories` | catalog | Admin | Tạo Danh mục |
| PATCH | `categories/{id}` | catalog | Admin | Sửa, đổi Danh mục cha, đổi thứ tự |
| DELETE | `categories/{id}` | catalog | Admin | Chỉ khi không còn Sản phẩm hay Danh mục con |
| GET | `products` | catalog | Admin | Danh sách, mọi trạng thái |
| POST | `products` | catalog | Admin | Tạo Sản phẩm ở trạng thái `draft` |
| GET | `products/{id}` | catalog | Admin | Chi tiết |
| PATCH | `products/{id}` | catalog | Admin | Sửa thông tin |
| DELETE | `products/{id}` | catalog | Admin | Chỉ Sản phẩm `draft`: chưa từng bán nên chưa có trong đơn (BR-CAT-09) |
| POST | `products/{id}/publish` | catalog | Admin | `draft` → `active` |
| POST | `products/{id}/archive` | catalog | Admin | Ngừng bán (`archived`) |
| POST | `products/{id}/variants` | catalog | Admin | Tạo Biến thể, hoặc sinh ma trận size × màu (US-802) |
| PATCH | `products/{id}/variants/{variant_id}` | catalog | Admin | Sửa Giá bán, trạng thái. Hạ Giá bán xuống ≤ Giá khuyến mãi đang hoặc sắp hiệu lực thì `422 LIST_PRICE_BELOW_SALE_PRICE` (BR-PRC-05) |
| POST | `products/{id}/images` | catalog | Admin | Upload ảnh theo màu |
| PATCH | `products/{id}/images/{image_id}` | catalog | Admin | Đổi thứ tự ảnh |
| DELETE | `products/{id}/images/{image_id}` | catalog | Admin | Xoá ảnh |
| GET | `sizes` | catalog | Admin | Danh sách size |
| POST | `sizes` | catalog | Admin | Thêm size (US-805) |
| PATCH | `sizes/{id}` | catalog | Admin | Sửa, ẩn bằng `is_active = false`; không có DELETE |
| GET | `colors` | catalog | Admin | Bảng màu |
| POST | `colors` | catalog | Admin | Thêm màu (US-805) |
| PATCH | `colors/{id}` | catalog | Admin | Sửa, ẩn bằng `is_active = false`; không có DELETE |
| GET | `sale-prices` | catalog | Admin | Danh sách Giá khuyến mãi |
| POST | `sale-prices` | catalog | Admin | Tạo cho một Biến thể hoặc mọi Biến thể của một Sản phẩm (US-804) |
| PATCH | `sale-prices/{id}` | catalog | Admin | Sửa giá, thời gian; kết thúc sớm bằng cách sửa `ends_at` |
| DELETE | `sale-prices/{id}` | catalog | Admin | Chỉ khi chưa bắt đầu |
| GET | `vouchers` | promotions | Admin | Danh sách kèm số lượt đã dùng |
| POST | `vouchers` | promotions | Admin | Tạo Voucher |
| PATCH | `vouchers/{id}` | promotions | Admin | Sửa, vô hiệu (`is_active = false`). Không có DELETE vì Voucher có Lượt dùng |
| GET | `staff` | identity | Admin | Danh sách Tài khoản Staff |
| POST | `staff` | identity | Admin | Tạo Tài khoản Staff (Tài khoản Admin chỉ tạo bằng lệnh) |
| PATCH | `staff/{id}` | identity | Admin | Sửa, vô hiệu (`is_active = false`, mọi phiên mất hiệu lực ngay) |
| GET | `settings/ordering` | ordering | Admin | Ngưỡng miễn phí ship, Hạn mức COD |
| PATCH | `settings/ordering` | ordering | Admin | Sửa hai giá trị trên |
| GET | `settings/shipping` | shipping | Admin | Phí ship dự phòng |
| PATCH | `settings/shipping` | shipping | Admin | Sửa Phí ship dự phòng |
| GET | `settings/ghn-locations` | shipping | Admin | Phường/xã chưa có ánh xạ sang GHN (US-1004) |
| PATCH | `settings/ghn-locations/{ward_code}` | shipping | Admin | Gán ID tỉnh, quận, phường của GHN cho một phường/xã |
| GET | `reports/revenue` | ordering | Admin | Báo cáo Doanh thu (BR-REV-01, BR-REV-02) |
| GET | `reports/paid-orders.csv` | ordering | Admin | Danh sách đơn đã thu tiền theo ngày, để gửi cho kế toán |

**Module sở hữu endpoint.** Mỗi endpoint nằm trong `api/` của đúng một module (cột Module). Màn cần dữ liệu của nhiều module thì Frontend gọi nhiều endpoint, hoặc endpoint đặt ở module cao nhất trong số đó và lấy phần còn lại qua `contracts` của module lớp dưới. Ví dụ `stock` (`inventory`) lấy SKU và tên qua `catalog.contracts`; còn chi tiết Khách hàng (`identity`) không đọc được Đơn hàng, nên Frontend lấy lịch sử đơn bằng `GET orders?customer_id=`.

### 4.3. Webhook: `/api/v1/webhooks/`

| Method | Path | Module | Xác thực | Phản hồi |
|---|---|---|---|---|
| GET | `vnpay/ipn` | payments | Chữ ký HMAC-SHA512 | JSON `{"RspCode": "00", "Message": "Confirm Success"}` theo đặc tả VNPay |
| POST | `momo/ipn` | payments | Chữ ký HMAC-SHA256 | HTTP 204 |
| POST | `ghn` | shipping | Token bí mật trong header + IP allow-list **[Cần xác minh cơ chế GHN hỗ trợ]** | HTTP 200 |

Webhook luôn trả thành công nhanh sau khi lưu dữ liệu gốc và chống trùng; việc xử lý nghiệp vụ chạy qua sự kiện. Đây là phần duy nhất của Django mở ra internet.

### 4.4. Vận hành

| Path | Mô tả |
|---|---|
| `/healthz` | Tiến trình còn sống |
| `/readyz` | Kết nối được PostgreSQL. Không kiểm tra Redis, để API vẫn phục vụ khi Redis lỗi ([10-nfr.md](./10-nfr.md) mục 2) |
| `/api/schema/`, `/api/docs/` | OpenAPI và Swagger UI (chỉ local và staging nội bộ, tắt trên production) |
| `/dev/fake-gateway/…` | Trang Fake Gateway (chỉ có khi `FAKE_PROVIDERS_ENABLED = true`, tức local và test) |
