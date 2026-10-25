# 01. Bối cảnh hệ thống (C4 mức 1 và 2)

> Trạng thái: **Bản nháp chờ review**. Thuật ngữ dùng theo [GLOSSARY.md](../../GLOSSARY.md).

## 1. Mức 1: hệ thống và các bên liên quan

```mermaid
graph TB
    guest([Khách vãng lai / Khách hàng])
    staff([Staff / Admin])

    subgraph system [Hệ thống Fashion Store]
        sf[Storefront<br/>Next.js - làm sau]
        bo[Back-office<br/>Next.js - làm sau]
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
    sf --> be
    bo --> be
    be <--> vnpay
    be <--> momo
    be <--> ghn
    be --> google
    be --> mail
    be --> sentry
```

| Bên ngoài | Hệ thống gọi tới | Gọi vào hệ thống |
|---|---|---|
| VNPay, MoMo | Tạo link thanh toán, truy vấn giao dịch (đối soát) | IPN báo kết quả thanh toán |
| GHN | Báo giá phí ship, tạo vận đơn, truy vấn trạng thái | Webhook báo trạng thái vận đơn |
| Google | Lấy khoá công khai để xác minh `id_token` | — |
| Email | Gửi email (SMTP / SES) | — |
| Sentry | Gửi lỗi và thông tin hiệu năng | — |

Giai đoạn này **chỉ làm Backend**. Storefront và back-office được thể hiện để rõ ai sẽ gọi API.

## 2. Mức 2: các container của Backend

```mermaid
graph TB
    client[Storefront / Back-office / Swagger UI]

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

    client -->|HTTPS JSON| api
    ext -->|IPN, webhook| api
    api --> pg
    api --> redis
    api --> files
    api --> ext
    relay -->|đọc outbox| pg
    relay -->|đẩy task| redis
    beat -->|đẩy task theo lịch| redis
    worker -->|nhận task| redis
    worker --> pg
    worker --> ext
```

| Container | Vai trò | Số bản chạy |
|---|---|---|
| API | Xử lý request HTTP: storefront, back-office, webhook | ≥ 2 trên AWS, scale theo CPU |
| Celery worker | Chạy handler sự kiện, gửi email, gọi API ngoài, job đối soát | ≥ 1, scale theo độ dài queue |
| Celery Beat | Đẩy job theo lịch (huỷ đơn hết hạn, đối soát, hoàn tất đơn) | **Đúng 1** |
| Outbox relay | Đọc bảng `outbox` rồi đẩy sự kiện sang Celery | **Đúng 1** (có khoá chống chạy trùng) |
| PostgreSQL | Dữ liệu nghiệp vụ, outbox, lịch job | 1 (Multi-AZ trên AWS) |
| Redis | Broker Celery, cache, throttling, idempotency key | 1 |

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

    payments -. "sự kiện: payment-succeeded" .-> ordering
    shipping -. "sự kiện: shipment-delivered" .-> ordering
    ordering -. "sự kiện: order-placed, order-cancelled…" .-> notifications
    identity -. "sự kiện: customer-erased" .-> ordering
```

Mũi tên liền: gọi trực tiếp qua `contracts.py`. Mũi tên đứt: thông báo ngược lên bằng sự kiện.

## 4. Luồng chính: đặt hàng thanh toán VNPay

```mermaid
sequenceDiagram
    participant C as Client
    participant API as Django API
    participant DB as PostgreSQL
    participant R as Relay + Celery
    participant V as VNPay

    C->>API: POST /store/checkout (Idempotency-Key)
    API->>DB: Tạo Order PENDING_PAYMENT + Giữ hàng 15' + outbox(order-placed)
    API-->>C: 201 {order_code}
    C->>API: POST /store/orders/{code}/payments {method: vnpay}
    API->>DB: Tạo Payment PENDING
    API-->>C: {redirect_url}
    C->>V: Khách thanh toán
    V->>API: IPN (có chữ ký)
    API->>DB: Kiểm tra chữ ký, chống trùng, Payment SUCCEEDED + outbox(payment-succeeded)
    API-->>V: RspCode 00
    R->>DB: Đọc outbox
    R->>API: (worker) handler ordering: Order → PLACED, chuyển Giữ hàng thành trừ kho
    Note over R: handler notifications gửi email "Thanh toán thành công"
    V-->>C: Chuyển về Return URL
    C->>API: GET /store/orders/{code} (hỏi lại trạng thái)
```

Nếu IPN không tới, job `reconcile_pending_payments` (mỗi 5 phút) truy vấn VNPay và xử lý giống hệt như khi nhận IPN.
