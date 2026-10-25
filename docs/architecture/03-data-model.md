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
```

- `shared_outbox_event`: index một phần (partial index) trên `occurred_at WHERE dispatched_at IS NULL` để relay đọc nhanh.
- `shared_processed_event`: khoá chính ghép `(event_id, handler)`. Một sự kiện có thể được nhiều handler xử lý, và mỗi handler chỉ xử lý một lần.

## 2. `identity`

```mermaid
erDiagram
    identity_user ||--o{ identity_address : "có"
    identity_user ||--o{ identity_refresh_token : "có"
    identity_user ||--o{ identity_consent : "đồng ý"
    identity_user {
        uuid id PK
        string email UK "lowercase"
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
        uuid user_id FK
        string recipient_name
        string phone
        string ward_code FK
        string street
        bool is_default
    }
    identity_refresh_token {
        uuid jti PK
        uuid user_id FK
        uuid family_id
        string token_hash "sha256"
        timestamptz expires_at
        timestamptz used_at
        timestamptz revoked_at
    }
    identity_consent {
        uuid id PK
        uuid user_id FK "null với Khách vãng lai"
        string subject_phone "Khách vãng lai"
        string purpose "data_processing | marketing"
        string policy_version
        string channel "register | checkout"
        bool granted
    }
    identity_erasure_request {
        uuid id PK
        uuid user_id FK
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

Ràng buộc: `UNIQUE(lower(email))`; mỗi user tối đa một `identity_address` có `is_default = true` (unique có điều kiện).

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
        string reference "mã đơn"
        uuid stock_item_id FK
        int quantity
        string status "active | committed | released"
        timestamptz expires_at
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
- Số bán được = `on_hand − reserved` (BR-INV-02). Cột `reserved` được cập nhật cùng transaction với `inventory_stock_reservation`, nên không phải cộng dồn khi đọc.
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
        string reference "mã đơn"
        uuid customer_id FK
        string phone
        bigint discount
        string status "redeemed | released"
    }
```

- `UNIQUE(voucher_id, reference)`.
- Đếm lượt dùng: khoá dòng `promotions_voucher` bằng `select_for_update` khi redeem để không vượt `usage_limit` lúc nhiều người dùng cùng lúc.

## 6. `payments`

```mermaid
erDiagram
    payments_payment ||--o{ payments_payment_event : "nhận"
    payments_payment ||--o{ payments_refund : "hoàn"
    payments_payment {
        uuid id PK
        string reference "mã đơn"
        string method "vnpay | momo | cod"
        bigint amount
        string status "pending | succeeded | failed | expired"
        string provider_txn_ref UK
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
        string status "requested | completed"
        string provider_refund_ref
        uuid recorded_by FK
        timestamptz completed_at
    }
```

- `UNIQUE(provider, provider_event_id)` trên `payments_payment_event` để chống xử lý IPN trùng (BR-PAY-03).
- `provider_txn_ref` là mã gửi sang cổng thanh toán (ví dụ `vnp_TxnRef`), mỗi lần thử thanh toán sinh một mã mới.

## 7. `shipping`

```mermaid
erDiagram
    shipping_shipment ||--o{ shipping_shipment_event : "nhận"
    shipping_shipment {
        uuid id PK
        string reference UK "mã đơn"
        string provider "ghn | fake"
        string provider_order_code UK
        string status "created | picking | in_transit | delivered | returning | returned"
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
```

`shipping_ghn_location_mapping` dùng để đổi mã địa chỉ 2 cấp của hệ thống sang ID của GHN, phòng trường hợp GHN vẫn dùng 3 cấp (xem [06-integrations.md](./06-integrations.md)).

## 8. `ordering`

```mermaid
erDiagram
    ordering_cart ||--o{ ordering_cart_item : "chứa"
    ordering_order ||--|{ ordering_order_line : "gồm"
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
        string code UK "FS2610-000123"
        uuid customer_id FK
        string status "FSM"
        string payment_method
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
        timestamptz expires_at "PENDING_PAYMENT"
        timestamptz delivered_at
        string cancel_reason
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
- `ordering_order_code_sequence` (không vẽ): một sequence PostgreSQL theo tháng để sinh mã đơn.
- Lịch sử trạng thái `ordering_order` và mọi thay đổi `payments_*`, `inventory_stock_item` được ghi bằng `django-pghistory`.
- Index: `(contact_phone, code)` cho tra cứu của Khách vãng lai; `(status, created_at)` cho back-office; partial index `expires_at WHERE status = 'PENDING_PAYMENT'` cho job huỷ đơn.

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

Khi xử lý yêu cầu xoá dữ liệu:

| Bảng | Cột bị ẩn danh |
|---|---|
| `identity_user` | `email` → `erased+<id>@invalid`, `full_name`, `phone` → rỗng, `is_active = false`, `anonymized_at` |
| `identity_address` | Xoá |
| `ordering_order` | `contact_name`, `contact_phone`, `contact_email`, `ship_street` → giá trị ẩn danh; giữ `ship_ward_code`, số tiền, Dòng đơn hàng |
| `ordering_cart` | Xoá |
| `identity_consent`, `identity_erasure_request` | **Giữ** làm bằng chứng tuân thủ |
