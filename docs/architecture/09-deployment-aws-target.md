# 09. Kiến trúc triển khai trên AWS (mục tiêu)

> Trạng thái: **Target – chưa triển khai**. Tài liệu này mô tả kiến trúc đích để định hướng; sẽ được chi tiết hoá sau khi hệ thống chạy ổn ở local và nghiệm thu xong với sandbox.
> Region: **ap-southeast-1 (Singapore)**. Lưu ý yêu cầu hồ sơ chuyển dữ liệu ra nước ngoài (CMP-08 trong [06-compliance.md](../business/06-compliance.md)).
> Quyết định nền tảng: [ADR 0009](../adr/0009-nextjs-bff-django-private.md) (Next.js là BFF, chạy cùng VPC; Django chỉ public webhook).

## 1. Sơ đồ

```mermaid
graph TB
    users([Người dùng]) --> cf[CloudFront + WAF]
    providers([VNPay · MoMo · GHN]) -->|IPN / webhook| cf
    cf -->|/media/*| s3[(S3: ảnh Sản phẩm)]
    cf -->|trang storefront, back-office<br/>và /api/v1/webhooks/*| alb[ALB public<br/>chỉ nhận từ CloudFront]

    subgraph vpc [VPC - 2 Availability Zone]
        subgraph private [Private subnet]
            sf[ECS Fargate: storefront Next.js × 2+]
            bo[ECS Fargate: back-office Next.js × 1+]
            ialb[ALB nội bộ]
            api[ECS Fargate: api × 2+]
            worker[ECS Fargate: worker × 1+]
            beat[ECS Fargate: beat × 1]
            relay[ECS Fargate: relay × 1]
            rds[(RDS PostgreSQL 18<br/>Multi-AZ)]
            redis[(ElastiCache Redis OSS)]
        end
        nat[NAT Gateway]
    end

    alb -->|host storefront| sf
    alb -->|host back-office| bo
    alb -->|/api/v1/webhooks/*| api
    sf -->|X-Client-IP + X-BFF-Secret| ialb
    bo -->|X-Client-IP + X-BFF-Secret| ialb
    ialb --> api
    api --> rds
    api --> redis
    worker --> rds
    worker --> redis
    beat --> rds
    beat --> redis
    relay --> rds
    relay --> redis
    worker --> nat
    api --> nat
    nat --> providers
    worker --> ses[Amazon SES]
    api --> s3
    secrets[Secrets Manager] -.-> api
    secrets -.-> worker
    secrets -.-> beat
    secrets -.-> relay
    secrets -.-> sf
    secrets -.-> bo
    logs[CloudWatch Logs] -.-> api
    sentry[Sentry] -.-> api
```

Từ internet chỉ vào được Django qua đúng một đường: `/api/v1/webhooks/*`. Mọi API còn lại (`/api/v1/store/`, `/api/v1/backoffice/`) chỉ nhận request từ Next.js qua ALB nội bộ.

## 2. Thành phần

| Thành phần | Dịch vụ AWS | Ghi chú |
|---|---|---|
| Storefront, back-office | **ECS Fargate**, image Next.js build từ repo frontend | Là BFF cho mọi request tới Django ([ADR 0009](../adr/0009-nextjs-bff-django-private.md)). Gửi IP thật của người dùng trong `X-Client-IP` kèm `X-BFF-Secret` |
| API, worker, beat, relay | **ECS Fargate**, cùng một image Django trên ECR, khác lệnh chạy | API scale theo CPU; beat luôn đúng 1 task; relay chạy 1 task, lúc deploy có thể chồng 2 (mục 4) |
| Load balancer | **ALB public** sau CloudFront; **ALB nội bộ** cho Next.js gọi Django | ALB public chỉ nhận từ dải IP của CloudFront (security group dùng managed prefix list), chia theo host (storefront, back-office) và path (`/api/v1/webhooks/*` → api). ALB nội bộ không có địa chỉ public |
| Database | **RDS for PostgreSQL 18**, Multi-AZ | Backup tự động 7 ngày, PITR; bật `unaccent`, `pg_trgm`, `btree_gist` **[Cần xác minh RDS đã hỗ trợ bản 18]**. Celery Beat đọc lịch job từ đây (`DatabaseScheduler`) |
| Redis | **ElastiCache for Redis OSS** | Broker Celery, cache, throttle, cache `token_version`. `maxmemory-policy noeviction`, mọi key cache có TTL. `Idempotency-Key` **không** nằm ở Redis mà ở PostgreSQL. Dùng Redis 7.2 ở local để khớp **[Cần xác minh phiên bản ElastiCache hiện có]**. Có thể đổi sang ElastiCache Valkey mà không phải sửa code |
| Ảnh | **S3** + **CloudFront** | `django-storages` S3; ảnh public qua CloudFront `/media/*` |
| Email | **Amazon SES** | Xác minh domain, SPF/DKIM/DMARC |
| Bí mật | **Secrets Manager** | Khoá JWT, khoá mã hoá RefreshReplay riêng (32 byte + key ID), mật khẩu DB, secret VNPay/MoMo/GHN, `BFF_SHARED_SECRET`. Mỗi task (api, worker, beat, relay, storefront, back-office) chỉ nhận secret nó cần |
| Log | **CloudWatch Logs** (log JSON từ structlog) | Giữ 30 ngày **[Giả định]** |
| Lỗi, hiệu năng | **Sentry** | |
| Bảo vệ | **WAF** trên CloudFront | Chặn bot, rate limit thô. Host back-office chỉ cho phép IP văn phòng hoặc VPN ([ADR 0004](../adr/0004-custom-nextjs-admin.md)). Webhook đi qua allow-list IP nếu nhà cung cấp công bố |
| IP ra ngoài cố định | **NAT Gateway** có Elastic IP | Một số cổng thanh toán yêu cầu khai báo IP server **[Cần xác minh]** |

STOREFRONT_ORIGIN production là origin HTTPS cấu hình cố định của storefront, không lấy từ request. Khoá RefreshReplay được cấp qua Secrets Manager; khi xoay giữ key cũ qua cửa sổ 10 giây và thời gian rolling deploy, mọi replica đọc cùng key ring. JWT signing key không dùng làm key mã hoá replay.

## 3. Môi trường

| Môi trường | Mục đích | Adapter |
|---|---|---|
| `staging` | Nghiệm thu, dùng sandbox VNPay/MoMo/GHN; có đủ storefront và back-office Next.js | Sandbox |
| `production` | Chạy thật | Thật |

## 4. Triển khai

1. CI chạy `make lint` + `make test`.
2. Build image, đẩy lên ECR.
3. Chạy migration bằng một ECS task chạy một lần (`manage.py migrate`) **trước** khi cập nhật service.
4. Cập nhật lần lượt các ECS service (rolling update).
5. Migration phải **tương thích ngược** với code đang chạy (thêm cột trước, xoá cột ở bản phát hành sau).

Service `beat` dùng cấu hình deploy `minimumHealthyPercent = 0`, `maximumPercent = 100`: task cũ dừng hẳn rồi task mới mới chạy, nên không lúc nào có hai bản cùng chạy, vì beat chạy trùng sẽ đẩy job hai lần. Đổi lại, beat ngừng vài chục giây mỗi lần deploy; việc này chấp nhận được vì job theo lịch chỉ bị trễ, không mất.

Service `relay` dùng rolling update mặc định (`minimumHealthyPercent = 100`, `maximumPercent = 200`): task mới chạy xong rồi task cũ mới dừng, nên relay không ngừng khi deploy. Trong lúc chuyển giao có hai bản relay cùng chạy, và việc này an toàn vì mỗi bản chỉ lấy các dòng outbox chưa bị bản khác khoá (`FOR UPDATE SKIP LOCKED`, xem [07](./07-async-events-jobs.md) mục 1).

Next.js deploy từ repo frontend, độc lập với Django. Thay `BFF_SHARED_SECRET` thì cập nhật Django trước để chấp nhận cả secret cũ lẫn mới, rồi mới cập nhật Next.js.

Công cụ hạ tầng (Terraform hoặc AWS CDK) sẽ chọn khi bắt đầu giai đoạn này.

## 5. Chi phí ước tính

Sẽ tính chi tiết khi bắt đầu giai đoạn AWS. Thành phần đáng kể nhất dự kiến là RDS Multi-AZ, NAT Gateway và ECS Fargate (gồm cả các task Next.js). Không có Kafka/MSK ([ADR 0007](../adr/0007-events-outbox-celery-no-kafka.md)).
