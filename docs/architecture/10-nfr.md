# 10. Yêu cầu phi chức năng

> Trạng thái: **Bản nháp chờ review**. Các con số là mục tiêu cho MVP với tải khoảng 500–5.000 đơn/ngày; mục có nhãn **[Giả định]** cần xác nhận.

## 1. Hiệu năng

| Chỉ số | Mục tiêu **[Giả định]** |
|---|---|
| p95 thời gian phản hồi API đọc (danh sách, chi tiết Sản phẩm, giỏ) | ≤ 300 ms |
| p95 `POST /store/checkout` khi báo giá GHN đã có trong cache | ≤ 800 ms |
| Tải đỉnh khi có khuyến mãi | 50 request/giây vào API, 10 đơn/giây, không bán vượt Tồn kho |
| Thời gian từ IPN tới đơn chuyển `PLACED` | p95 ≤ 5 giây |
| Email gửi sau sự kiện | p95 ≤ 1 phút |

Cách đạt được:

- Không có N+1 query: `django-zeal` bật trong test, test fail nếu có.
- Danh sách Sản phẩm dùng `catalog_variant.is_available` (bản sao) để lọc "còn hàng" mà không phải join sang `inventory`.
- Cache trong Redis: cây danh mục (5 phút), báo giá GHN (10 phút), dữ liệu địa giới (1 ngày).
- Checkout không gọi HTTP ra ngoài bên trong transaction. Phí ship lấy từ cache báo giá (thường đã có từ bước `checkout/quote`) trước khi mở transaction, nên khoá dòng chỉ được giữ trong lúc ghi DB.
- Trong transaction, checkout khoá toàn bộ `inventory_stock_item` theo variant_id, rồi toàn bộ Variant theo id để kiểm tra lại giá, sau đó mới khoá Voucher, để tránh deadlock khi nhiều người mua cùng lúc.

## 2. Độ sẵn sàng và phục hồi

| Chỉ số | Mục tiêu **[Giả định]** |
|---|---|
| Độ sẵn sàng của API (production) | 99,5% / tháng |
| RPO (dữ liệu tối đa có thể mất) | ≤ 5 phút (RDS PITR) |
| RTO (thời gian khôi phục) | ≤ 1 giờ |
| Khi GHN lỗi | Vẫn checkout được (phí ship dự phòng) |
| Khi VNPay/MoMo lỗi | Vẫn đặt được đơn COD |
| Khi Redis lỗi | API vẫn chạy, kể cả checkout: cache và throttle fail-open (chỉ còn rate limit thô của WAF), kiểm tra `token_version` đọc thẳng PostgreSQL, `Idempotency-Key` lưu ở PostgreSQL. Outbox/EventDelivery và EmailLog giữ công việc còn chờ trong PostgreSQL; relay/job quét khôi phục khi broker và worker hoạt động lại, kể cả task từng được enqueue rồi mất. `/readyz` chỉ kiểm tra PostgreSQL, nên ALB không rút task API khi Redis lỗi |

## 3. Bảo mật

Xem [05-auth-security.md](./05-auth-security.md). Thêm:

- Không lưu dữ liệu thẻ (thuộc phạm vi của VNPay, MoMo).
- Mã hoá khi truyền (TLS 1.2+) và khi lưu (RDS, S3, ElastiCache bật encryption at rest).
- Django API chỉ nhận request từ Next.js (BFF) qua ALB nội bộ; từ internet chỉ vào được `/api/v1/webhooks/*` ([ADR 0009](../adr/0009-nextjs-bff-django-private.md), [09](./09-deployment-aws-target.md)).
- Rà soát lỗ hổng phụ thuộc trong mỗi lần chạy CI.

## 4. Quan sát hệ thống (observability)

| Loại | Công cụ | Nội dung |
|---|---|---|
| Log | `structlog` → stdout (JSON) → CloudWatch | Mỗi dòng có `request_id`, `user_id` (nếu có), `order_code` (nếu có); che PII |
| Lỗi | Sentry | API, Celery task, relay |
| Health | `/healthz` (tiến trình sống), `/readyz` (kết nối được PostgreSQL) | Dùng cho ALB và ECS health check |
| Chỉ số nghiệp vụ cần cảnh báo | Sentry / CloudWatch | Outbox chưa lập delivery hoặc delivery pending tồn quá 1.000; tuổi delivery pending cũ nhất; EmailLog queued/sending quá 5 phút hoặc failed; heartbeat relay/job khôi phục quá 3 phút; ErasureRequest processing có handler thiếu/failed/rejected; Payment creation_status prepared/unknown quá lease; Thanh toán pending quá 30 phút; tỉ lệ đơn dùng Phí ship dự phòng > 10%; có delivery failed chưa xử lý; Cờ cần xử lý mở quá 24 giờ **[Giả định]** |

`request_id` lấy từ header `X-Request-ID` nếu có, ngược lại tự sinh; được đưa vào cả sự kiện outbox để lần theo một luồng từ API tới email.

## 5. Khả năng mở rộng

| Khi | Làm gì |
|---|---|
| API chậm do CPU | Tăng số task ECS của API |
| Queue Celery dài | Tăng worker; tách worker riêng cho queue `emails` / `integrations` |
| Tìm kiếm chậm hoặc cần tìm sai chính tả | Thêm Meilisearch (giai đoạn 2) |
| Cần phát lại sự kiện cho hệ thống mới, hoặc lưu lượng > 1.000 sự kiện/giây | Thêm adapter Kafka ([ADR 0007](../adr/0007-events-outbox-celery-no-kafka.md)) |
| Một module cần scale hoặc deploy độc lập | Tách module đó thành service. Ranh giới `contracts.py` và sự kiện đã có, nhưng trước đó phải bỏ các FK chéo module ([ADR 0006](../adr/0006-modular-monolith.md) cho phép) và tách bảng của module khỏi chuỗi migration chung |

## 6. Chất lượng code

| Cổng chặn trong CI | Điều kiện để qua |
|---|---|
| `ruff check`, `ruff format --check` | Không lỗi |
| `mypy` | Không lỗi (`--strict` cho `services`, `selectors`, `contracts`) |
| `lint-imports` | Không vi phạm ranh giới module |
| `pytest` | Toàn bộ test qua |
| Độ phủ test | ≥ 80% branch coverage cho `services/` và `handlers.py`, tính riêng từng module, không đặt ngưỡng toàn repo ([12-testing-strategy.md](./12-testing-strategy.md) mục 8) |
| OpenAPI | Schema sinh ra trùng với `backend/openapi.yaml` đã commit |
| Migration | Không thiếu migration (`makemigrations --check`), không có nhánh migration xung đột trong cùng app; số migration được lặp giữa các app |
| Lỗ hổng phụ thuộc | Không có lỗ hổng mức cao |

## 7. Bản địa hoá

- Thời gian lưu UTC, hiển thị `Asia/Ho_Chi_Minh`.
- `error.message` và email dịch vi/en bằng `gettext`; mặc định `vi`.
- Nội dung Sản phẩm, danh mục chỉ tiếng Việt.
- Số tiền VND là số nguyên; định dạng hiển thị ("250.000 ₫") do Frontend lo.
