# 03. Mô hình dữ liệu

> Trạng thái: **Bản nháp chờ review**. Tên bảng có tiền tố theo module ([ADR 0006](../adr/0006-modular-monolith.md)).
> Quy ước chung cho mọi bảng: `id` UUID, `created_at`, `updated_at` (kế thừa `shared.models.BaseModel`). Tiền là `bigint` số đồng VND. Thời gian lưu UTC.

## 1. `shared`

```mermaid
erDiagram
    shared_province ||--o{ shared_ward : "có"
    shared_province {
        string code PK "mã Cục Thống kê"
        string name
    }
    shared_ward {
        string code PK
        string province_code FK
        string name
    }
    shared_outbox_event {
        uuid id PK "= event_id"
        string event_type
        int schema_version
        jsonb payload
        timestamptz occurred_at
        timestamptz dispatched_at "null = chưa gửi"
        int attempts
    }
    shared_processed_event {
        uuid event_id PK
        string handler PK
        timestamptz processed_at
    }
    shared_failed_event {
        uuid event_id PK
        string handler PK
        text error
        timestamptz failed_at
        timestamptz retried_at
    }
    shared_idempotency_key {
        string scope PK "endpoint + Người mua"
        uuid key PK
        string request_hash
        int response_status
        jsonb response_body
        timestamptz created_at
    }
```

- `shared_outbox_event`: index một phần (partial index) trên `occurred_at WHERE dispatched_at IS NULL` để relay đọc nhanh. Payload không chứa secret hay PII.
- `shared_processed_event`: khoá chính ghép `(event_id, handler)`. Một sự kiện có thể được nhiều handler xử lý, và mỗi handler chỉ xử lý một lần.
- `shared_failed_event`: ghi khi một cặp (sự kiện, handler) hết retry; `manage.py retry_failed_events` đọc bảng này.
- `shared_idempotency_key`: lưu kết quả lần đầu của các POST có `Idempotency-Key`. Lưu ở PostgreSQL thay vì Redis vì liên quan tới tiền và không được mất khi Redis bị xoá key. Job `shared.purge_idempotency_keys` xoá bản ghi quá 24 giờ.

## 2. `identity`

```mermaid
erDiagram
    identity_account ||--o{ identity_address : "có"
    identity_account ||--o{ identity_refresh_token : "có"
    identity_account ||--o{ identity_consent : "đồng ý"
    identity_account {
        uuid id PK
        string email UK "lowercase, duy nhất cho mọi kind"
        string password "argon2"
        string kind "customer | staff | admin"
        string full_name
        string phone
        string language "vi | en"
        int token_version
        bool is_active
        bool email_verified
        timestamptz anonymized_at
    }
    identity_address {
        uuid id PK
        uuid account_id FK
        string recipient_name
        string phone
        string ward_code FK
        string street
        bool is_default
    }
    identity_refresh_token {
        uuid jti PK
        uuid account_id FK
        uuid family_id
        string token_hash "sha256"
        timestamptz expires_at
        timestamptz used_at
        timestamptz revoked_at
    }
    identity_consent {
        uuid id PK
        uuid account_id FK "null với Khách vãng lai"
        string subject_phone "Khách vãng lai"
        string purpose "data_processing | marketing"
        string policy_version
        string channel "register | checkout"
        bool granted
    }
    identity_erasure_request {
        uuid id PK
        uuid account_id FK
        string subject_phone
        string status "received | completed | rejected"
        timestamptz received_at
        timestamptz completed_at
        uuid handled_by FK
    }
    identity_customer_data_access_log {
        uuid id PK
        uuid staff_id FK
        uuid customer_id FK
        string subject_phone
        string action
    }
```

Ràng buộc: `UNIQUE(lower(email))` cho mọi `kind`, tức một email chỉ thuộc một Tài khoản (Staff muốn mua hàng phải dùng email khác); mỗi Tài khoản tối đa một `identity_address` có `is_default = true` (unique có điều kiện).

## 3. `catalog`

```mermaid
erDiagram
    catalog_category ||--o{ catalog_category : "cha - con"
    catalog_category ||--o{ catalog_product : "chứa"
    catalog_product ||--o{ catalog_product_color : "có màu"
    catalog_product_color ||--o{ catalog_product_image : "ảnh"
    catalog_product ||--|{ catalog_variant : "có"
    catalog_variant ||--o{ catalog_sale_price : "khuyến mãi"
    catalog_category {
        uuid id PK
        uuid parent_id FK
        string name "tiếng Việt"
        string slug UK
        int position
    }
    catalog_product {
        uuid id PK
        uuid category_id FK
        string name "tiếng Việt"
        string slug UK
        text description
        string status "draft | active | archived"
        int weight_grams
        tsvector search_vector
    }
    catalog_product_color {
        uuid id PK
        uuid product_id FK
        string color_code "WHT, BLK…"
        string color_name "tiếng Việt"
    }
    catalog_product_image {
        uuid id PK
        uuid product_color_id FK
        string file
        int position
    }
    catalog_variant {
        uuid id PK
        uuid product_id FK
        string sku UK
        string size
        uuid product_color_id FK
        bigint price
        bool is_available "bản sao từ inventory"
        string status "active | archived"
    }
    catalog_sale_price {
        uuid id PK
        uuid variant_id FK
        bigint price
        timestamptz starts_at
        timestamptz ends_at
    }
```

Ràng buộc và index:

- `UNIQUE(product_id, size, product_color_id)` trên `catalog_variant` (BR-CAT-02).
- `CHECK(price > 0)`.
- `catalog_sale_price`: `CHECK(starts_at < ends_at)`. Ràng buộc **không trùng thời gian** cho cùng Biến thể bằng `EXCLUDE USING gist (variant_id WITH =, tstzrange(starts_at, ends_at) WITH &&)` (BR-PRC-02). Ràng buộc "nhỏ hơn giá bán" (BR-PRC-01) được kiểm tra ở service, vì giá bán nằm ở bảng khác.
- Tìm kiếm: index GIN trigram trên `immutable_unaccent(lower(name))` của `catalog_product` (cần tạo một hàm `IMMUTABLE` bọc `unaccent`).

## 4. `inventory`

```mermaid
erDiagram
    inventory_warehouse ||--o{ inventory_stock_item : "chứa"
    inventory_stock_item ||--o{ inventory_stock_movement : "lịch sử"
    inventory_warehouse {
        uuid id PK
        string code UK
        string name
    }
    inventory_stock_item {
        uuid id PK
        uuid warehouse_id FK
        uuid variant_id FK
        int on_hand
        int reserved
    }
    inventory_stock_reservation {
        uuid id PK
        string reference "Mã đơn"
        uuid stock_item_id FK
        int quantity
        string status "active | committed | released"
        timestamptz expires_at "= ordering_order.expires_at"
    }
    inventory_stock_movement {
        uuid id PK
        uuid stock_item_id FK
        string kind "inbound | sale | reservation_commit | release | restock | adjustment"
        int delta
        string reference
        string reason
        uuid actor_id
    }
```

- `UNIQUE(warehouse_id, variant_id)`; `CHECK(on_hand >= 0)`, `CHECK(reserved >= 0)`, `CHECK(reserved <= on_hand)`.
- `on_hand` là Tồn kho; Số lượng bán được = `on_hand − reserved` (BR-INV-02). Cột `reserved` được cập nhật cùng transaction với `inventory_stock_reservation`, nên không phải cộng dồn khi đọc.
- `inventory_stock_reservation.expires_at` được truyền từ `ordering_order.expires_at` (nguồn duy nhất), không tự tính.
- Giữ hàng đã quá `expires_at` bị coi là không hợp lệ ngay cả khi job chưa kịp giải phóng ([ADR 0003](../adr/0003-postgres-redis-celery.md)).

## 5. `promotions`

```mermaid
erDiagram
    promotions_voucher ||--o{ promotions_voucher_redemption : "lượt dùng"
    promotions_voucher {
        uuid id PK
        string code UK "in hoa"
        string kind "percent | fixed"
        bigint value "% hoặc số tiền"
        bigint max_discount
        bigint min_order_value
        int usage_limit
        int per_customer_limit
        timestamptz starts_at
        timestamptz ends_at
        bool is_active
    }
    promotions_voucher_redemption {
        uuid id PK
        uuid voucher_id FK
        string reference "Mã đơn"
        uuid customer_id FK
        string phone
        bigint discount
        string status "redeemed | released"
    }
```

- `UNIQUE(voucher_id, reference)`.
- Đếm lượt dùng: khoá dòng `promotions_voucher` bằng `select_for_update` khi redeem để không vượt `usage_limit` lúc nhiều người dùng cùng lúc. Dòng Voucher được khoá **sau** các dòng Tồn kho (thứ tự khoá cố định, xem [02](./02-backend-structure.md) mục 9.1).
- `per_customer_limit` đếm các lượt `redeemed` trùng `customer_id` **hoặc** trùng `phone` với số điện thoại liên hệ của đơn đang đặt (BR-VCH-07). Cần index trên `(voucher_id, customer_id)` và `(voucher_id, phone)`.

## 6. `payments`

```mermaid
erDiagram
    payments_payment ||--o{ payments_payment_event : "nhận"
    payments_payment ||--o{ payments_refund : "hoàn"
    payments_payment {
        uuid id PK
        string reference "Mã đơn"
        string method "cod | online"
        string gateway "vnpay | momo, null với COD"
        bigint amount
        string status "pending | succeeded | failed | expired | cancelled"
        string provider_txn_ref UK "null với COD"
        timestamptz expires_at "hạn link, chỉ online"
        timestamptz paid_at
    }
    payments_payment_event {
        uuid id PK
        uuid payment_id FK
        string provider
        string provider_event_id
        string source "ipn | reconcile"
        jsonb raw_payload
        bool signature_valid
    }
    payments_refund {
        uuid id PK
        uuid payment_id FK
        bigint amount
        string reason
        string channel "gateway | bank_transfer"
        string status "requested | completed"
        string provider_refund_ref
        uuid recorded_by "không FK"
        timestamptz completed_at
    }
```

- `UNIQUE(provider, provider_event_id)` trên `payments_payment_event` để chống xử lý IPN trùng (BR-PAY-03).
- Mỗi lần thử thanh toán online là một Thanh toán mới, có `provider_txn_ref` mới (mã gửi sang Cổng thanh toán, ví dụ `vnp_TxnRef`) và `gateway` do Người mua chọn ở lần đó. `expires_at` = lúc đặt đơn + `PAYMENT_LINK_TTL` (phút thứ 10 kể từ khi đặt đơn), giống nhau cho mọi lần thử, để link không bao giờ sống quá Giữ hàng.
- Đơn COD có đúng một Thanh toán `method = cod`: tạo ở T2 (`pending`), `succeeded` khi GHN báo đã giao và thu tiền (T11), `cancelled` khi đơn bị huỷ hoặc Hoàn hàng.
- Hoàn tiền của đơn online có `channel = gateway`; Hoàn tiền Đổi trả của đơn COD gắn vào Thanh toán COD, `channel = bank_transfer`.
- `recorded_by` lưu id của Tài khoản Staff nhưng **không** khai báo FK: `payments` và `identity` cùng lớp nên không được phụ thuộc nhau ([ADR 0006](../adr/0006-modular-monolith.md)), giống `inventory_stock_movement.actor_id`.

## 7. `shipping`

```mermaid
erDiagram
    shipping_shipment ||--o{ shipping_shipment_event : "nhận"
    shipping_shipment {
        uuid id PK
        string reference UK "Mã đơn"
        string provider "ghn | fake"
        string provider_order_code UK "null khi requested"
        string status "requested | created | picking | in_transit | delivered | returning | returned | failed | cancelled"
        bigint fee
        bigint cod_amount
    }
    shipping_shipment_event {
        uuid id PK
        uuid shipment_id FK
        string provider_status
        string source "webhook | reconcile"
        jsonb raw_payload
        timestamptz occurred_at
    }
    shipping_ghn_location_mapping {
        string ward_code PK
        int ghn_province_id
        int ghn_district_id
        string ghn_ward_code
    }
    shipping_settings {
        uuid id PK
        bigint fallback_fee "Phí ship dự phòng"
    }
```

- `shipping_ghn_location_mapping` dùng để đổi mã địa chỉ 2 cấp của hệ thống sang ID của GHN, phòng trường hợp GHN vẫn dùng 3 cấp (xem [06-integrations.md](./06-integrations.md)).
- `shipping_shipment.fee` là phí GHN thực tính cho cửa hàng, khác `ordering_order.shipping_fee` là phí Người mua trả (bằng 0 khi được miễn phí ship).
- Vận đơn được tạo ở trạng thái `requested`, task nền gọi GHN rồi chuyển sang `created` hoặc `failed`.
- `shipping_settings` là singleton (một dòng duy nhất), Admin sửa qua back-office, lịch sử thay đổi ghi bằng `django-pghistory`.

## 8. `ordering`

```mermaid
erDiagram
    ordering_cart ||--o{ ordering_cart_item : "chứa"
    ordering_order ||--|{ ordering_order_line : "gồm"
    ordering_order ||--o{ ordering_order_flag : "cờ"
    ordering_order ||--o{ ordering_return_request : "đổi trả"
    ordering_return_request ||--|{ ordering_return_line : "gồm"
    ordering_cart {
        uuid id PK
        uuid customer_id FK "null với Khách vãng lai"
        string guest_token UK "cookie cart_token"
        timestamptz last_activity_at
    }
    ordering_cart_item {
        uuid id PK
        uuid cart_id FK
        uuid variant_id FK
        int quantity
        bigint price_when_added
    }
    ordering_order {
        uuid id PK
        string code UK "FS2610-7K3QZD"
        uuid customer_id FK "null với Khách vãng lai"
        string status "FSM"
        string payment_method "cod | online"
        string contact_name
        string contact_phone
        string contact_email
        string ship_ward_code FK
        string ship_street
        bigint subtotal
        bigint discount
        bigint shipping_fee
        bool shipping_fee_fallback
        bigint total
        string voucher_code
        string language
        bool invoice_requested
        jsonb invoice_info
        timestamptz expires_at "hạn Giữ hàng, nguồn duy nhất"
        timestamptz delivered_at
        string cancel_reason
    }
    ordering_order_flag {
        uuid id PK
        uuid order_id FK
        string kind
        text note
        timestamptz raised_at
        timestamptz resolved_at
        uuid resolved_by FK
    }
    ordering_settings {
        uuid id PK
        bigint free_shipping_threshold
        bigint cod_limit
    }
    ordering_order_line {
        uuid id PK
        uuid order_id FK
        uuid variant_id FK
        string product_name "snapshot"
        string sku "snapshot"
        string size "snapshot"
        string color_name "snapshot"
        bigint unit_price "snapshot"
        bigint list_price "snapshot"
        int discount_percent "snapshot"
        bigint voucher_discount "snapshot, phần Voucher phân bổ"
        int quantity
    }
    ordering_return_request {
        uuid id PK
        uuid order_id FK
        string status "recorded | received | accepted | rejected | refunded"
        string channel "hotline | zalo"
        string reason
        uuid recorded_by FK
    }
    ordering_return_line {
        uuid id PK
        uuid return_request_id FK
        uuid order_line_id FK
        int quantity
    }
```

- `CHECK(total = subtotal - discount + shipping_fee)` (BR-ORD-01), `CHECK(quantity > 0)`.
- `code`: `FS<YYMM>-` + 6 ký tự Crockford Base32 ngẫu nhiên, `UNIQUE`; trùng thì sinh lại. Không dùng sequence, để Mã đơn không lộ thứ tự hay số lượng đơn ([ADR 0008](../adr/0008-uuid-v7-primary-keys.md)).
- `expires_at` = lúc đặt + 15 phút (`RESERVATION_TTL`) với đơn online. Đây là nguồn duy nhất của hạn Giữ hàng, được truyền xuống `inventory_stock_reservation.expires_at`.
- `customer_id` null với đơn của Khách vãng lai; được gắn vào Tài khoản khi Khách hàng xác thực email trùng `contact_email` (không phân biệt hoa thường).
- `ordering_order_line.voucher_discount`: phần Voucher phân bổ cho dòng theo tỷ lệ giá trị dòng, phần lẻ dồn vào dòng cuối; `SUM(voucher_discount) = ordering_order.discount`. Dùng để tính Hoàn tiền khi Đổi trả một phần (BR-RET-07).
- `ordering_order_flag` (Cờ cần xử lý): `kind` ∈ `payment_amount_mismatch | unexpected_payment | shipping_fee_fallback | ghn_ward_unmapped | shipment_failed | shipment_after_cancel`. Partial `UNIQUE(order_id, kind) WHERE resolved_at IS NULL` để một vấn đề chỉ có một cờ đang mở. `resolved_by` FK tới `identity_account`.
- `ordering_settings` là singleton (một dòng duy nhất), Admin sửa qua back-office.
- `django-pghistory` ghi lịch sử của `ordering_order` (chỉ các field không phải PII: `status`, `payment_method`, `subtotal`, `discount`, `shipping_fee`, `total`, `cancel_reason`, `delivered_at`), `ordering_order_flag`, `ordering_settings`, `shipping_settings`, mọi thay đổi `payments_*` và `inventory_stock_item`. Không theo dõi các cột liên hệ của Đơn hàng để lịch sử không giữ lại PII sau khi ẩn danh.
- Index: `(contact_phone, code)` cho tra cứu của Khách vãng lai; `(status, created_at)` cho back-office; partial index `expires_at WHERE status = 'PENDING_PAYMENT'` cho job huỷ đơn; partial index `(kind, raised_at) WHERE resolved_at IS NULL` trên `ordering_order_flag` cho bộ lọc theo cờ.

## 9. `notifications`

```mermaid
erDiagram
    notifications_email_log {
        uuid id PK
        uuid event_id
        string template
        string language
        string to_address
        string status "queued | sent | failed"
        int attempts
        timestamptz sent_at
    }
```

`UNIQUE(event_id, template)` để một sự kiện không sinh hai email giống nhau.

## 10. Ẩn danh dữ liệu (CMP-05)

Điều kiện: yêu cầu xoá dữ liệu chỉ được hoàn thành khi mọi Đơn hàng của người đó đã ở trạng thái cuối (`COMPLETED`, `CANCELLED`, `RETURNED_TO_SENDER`). Khi đó `identity` phát `identity.customer-erased` chỉ mang `erasure_request_id`; mỗi module tự ẩn danh dữ liệu của mình, lấy đối tượng (Tài khoản hoặc số điện thoại) qua `identity.contracts.get_erasure_subject`. `shipping` và `payments` cùng lớp với `identity` nên không nghe sự kiện này; `ordering` gọi `redact_provider_payloads(reference)` của hai module đó cho từng Đơn hàng.

| Bảng | Module | Xử lý |
|---|---|---|
| `identity_account` | identity | `email` → `erased+<id>@invalid`, `full_name`, `phone` → rỗng, `is_active = false`, `anonymized_at` |
| `identity_address` | identity | Xoá |
| `ordering_order` | ordering | `contact_name`, `contact_phone`, `contact_email`, `ship_street` → giá trị ẩn danh; giữ `ship_ward_code`, số tiền, Dòng đơn hàng |
| `ordering_cart` | ordering | Xoá |
| `promotions_voucher_redemption` | promotions | `phone` → giá trị ẩn danh |
| `notifications_email_log` | notifications | `to_address` → giá trị ẩn danh |
| `shipping_shipment_event` | shipping (do `ordering` gọi) | Xoá PII trong `raw_payload` |
| `payments_payment_event` | payments (do `ordering` gọi) | Xoá PII trong `raw_payload` |
| Lịch sử pghistory của `ordering_order` | — | Không cần xử lý: chỉ theo dõi field không phải PII (mục 8) |
| `shared_outbox_event` | — | Không cần xử lý: payload sự kiện không chứa PII |
| `identity_consent`, `identity_erasure_request` | identity | **Giữ** làm bằng chứng tuân thủ |
