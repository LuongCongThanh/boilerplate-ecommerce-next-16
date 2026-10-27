# 01. Bối cảnh hệ thống (C4 mức 1 và 2)

> Trạng thái: **Bản nháp chờ review**. Thuật ngữ dùng theo [GLOSSARY.md](../../GLOSSARY.md).

## 1. Mức 1: hệ thống và các bên liên quan

```mermaid
graph TB
    guest([Người mua])
    staff([Staff / Admin])

    subgraph system [Hệ thống Fashion Store]
        sf[Storefront<br/>Next.js BFF - làm sau]
        bo[Back-office<br/>Next.js BFF - làm sau]
        be[Django Backend]
    end

    vnpay[VNPay]
    momo[MoMo]
    ghn[GHN]
    google[Google OAuth]
    mail[Dịch vụ email<br/>Mailpit ở local / SES trên AWS]
    sentry[Sentry]

    guest --> sf
    staff --> bo
    sf -->|mạng nội bộ VPC| be
    bo -->|mạng nội bộ VPC| be
    be <--> vnpay
    be <--> momo
    be <--> ghn
    be --> google
    be --> mail
    be --> sentry
```

| Bên ngoài | Hệ thống gọi tới | Gọi vào hệ thống |
|---|---|---|
| VNPay, MoMo | Tạo link thanh toán, truy vấn giao dịch (Đối soát) | IPN báo kết quả thanh toán |
| GHN | Báo giá phí ship, tạo vận đơn, truy vấn trạng thái | Webhook báo trạng thái vận đơn |
| Google | Lấy khoá công khai để xác minh `id_token` | — |
| Email | Gửi email (SMTP / SES) | — |
| Sentry | Gửi lỗi và thông tin hiệu năng | — |

Giai đoạn này **chỉ làm Backend**. Storefront và back-office được thể hiện để rõ ai sẽ gọi API.

Trình duyệt chỉ nói chuyện với Next.js. Next.js là BFF cho **mọi** request tới Django và chạy cùng VPC với Django ([ADR 0009](../adr/0009-nextjs-bff-django-private.md)). Từ internet, chỉ IPN và webhook của VNPay, MoMo, GHN gọi thẳng vào Django (`/api/v1/webhooks/*`).

## 2. Mức 2: các container của Backend

```mermaid
graph TB
    client[Next.js BFF<br/>storefront, back-office]

    subgraph backend [Django Backend - cùng 1 codebase, 1 Docker image]
        api[API<br/>gunicorn + Django + DRF]
        worker[Celery worker<br/>queue: default, events, emails, integrations]
        beat[Celery Beat<br/>lịch job]
        relay[Outbox relay<br/>manage.py run_outbox_relay]
    end

    pg[(PostgreSQL 18)]
    redis[(Redis)]
    files[(Ảnh Sản phẩm<br/>ổ đĩa local / S3)]
    ext[VNPay · MoMo · GHN · Google · Email]

    client -->|HTTPS JSON, mạng nội bộ| api
    ext -->|IPN, webhook - phần duy nhất public| api
    api --> pg
    api --> redis
    api --> files
    api --> ext
    relay -->|đọc outbox| pg
    relay -->|đẩy task| redis
    beat -->|đọc lịch job| pg
    beat -->|đẩy task theo lịch| redis
    worker -->|nhận task| redis
    worker --> pg
    worker --> ext
```

| Container | Vai trò | Số bản chạy |
|---|---|---|
| API | Xử lý request HTTP: storefront, back-office, webhook | ≥ 2 trên AWS, scale theo CPU |
| Celery worker | Chạy handler sự kiện, gửi email, gọi API ngoài, job Đối soát | ≥ 1, scale theo độ dài queue |
| Celery Beat | Đẩy job theo lịch (huỷ đơn hết hạn, Đối soát, hoàn tất đơn). Lịch lưu trong PostgreSQL (`DatabaseScheduler`) | **Đúng 1** |
| Outbox relay | Đọc bảng `outbox` rồi đẩy sự kiện sang Celery | **Đúng 1** (có khoá chống chạy trùng) |
| PostgreSQL | Dữ liệu nghiệp vụ, outbox, `Idempotency-Key`, lịch job | 1 (Multi-AZ trên AWS) |
| Redis | Broker Celery, cache, throttling, cache `token_version`. Đặt `noeviction`, mọi key cache có TTL | 1 |

## 3. Mức 3: module bên trong Backend

Chi tiết xem [02-backend-structure.md](./02-backend-structure.md).

```mermaid
graph TB
    notifications --> ordering
    ordering --> inventory
    ordering --> promotions
    ordering --> identity
    ordering --> catalog
    ordering --> payments
    ordering --> shipping
    inventory --> catalog
    promotions --> identity
    identity --> shared
    catalog --> shared
    payments --> shared
    shipping --> shared

    payments -. "sự kiện: payment-succeeded, refund-recorded…" .-> ordering
    shipping -. "sự kiện: shipment-created, shipment-delivered…" .-> ordering
    ordering -. "sự kiện: order-placed, order-cancelled…" .-> notifications
    identity -. "sự kiện: email-verified, customer-erased" .-> ordering
    identity -. "sự kiện: customer-registered, password-reset-requested" .-> notifications
```

Mũi tên liền: gọi trực tiếp qua `contracts.py`. Mũi tên đứt: thông báo ngược lên bằng sự kiện.

## 4. Luồng chính: đặt hàng thanh toán VNPay

```mermaid
sequenceDiagram
    participant B as Trình duyệt
    participant N as Next.js (BFF)
    participant API as Django API
    participant DB as PostgreSQL
    participant R as Relay + Celery
    participant V as VNPay

    B->>N: Đặt hàng
    N->>API: POST /store/checkout {payment_method: online, expected_total} + Idempotency-Key
    Note over API: Ngoài transaction: Giá áp dụng, Voucher, phí ship (cache báo giá), so với expected_total
    API->>DB: Một transaction: Giữ hàng (hạn 15'), lượt Voucher, Order PENDING_PAYMENT. Không ghi outbox
    API-->>N: 201 {order_code, lookup_token}
    N->>API: POST /store/orders/{code}/payments {gateway: vnpay} + X-Lookup-Token
    API->>DB: Tạo Payment pending (link hết hạn sau 10')
    API-->>N: {redirect_url}
    N-->>B: Chuyển sang VNPay
    B->>V: Người mua thanh toán
    V->>API: IPN có chữ ký (gọi thẳng /api/v1/webhooks/vnpay/ipn)
    API->>DB: Kiểm tra chữ ký, chống trùng, Payment succeeded + outbox(payment-succeeded)
    API-->>V: RspCode 00
    R->>DB: Đọc outbox
    R->>DB: (worker) handler ordering: T3, Order → PLACED, Giữ hàng thành trừ Tồn kho, outbox(order-placed)
    Note over R: handler notifications nhận order-placed (online) và gửi email "Thanh toán thành công"
    V-->>B: Chuyển về Return URL
    B->>N: Trang kết quả
    N->>API: GET /store/orders/{code} (hỏi lại trạng thái)
```

Nếu IPN không tới, job `reconcile_pending_payments` (mỗi 5 phút) truy vấn VNPay và xử lý giống hệt như khi nhận IPN.

Link thanh toán hết hạn ở phút 10, Giữ hàng ở phút 15. Khoảng đệm 5 phút dành cho IPN đến muộn và một vòng Đối soát. Nếu tiền vẫn về khi Đơn hàng không còn ở `PENDING_PAYMENT` (đã huỷ, hoặc đã được trả bởi một lần Thanh toán khác), hệ thống tự tạo Hoàn tiền và gắn Cờ cần xử lý `unexpected_payment` (BR-PAY-05).
