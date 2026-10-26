# 10. Yêu cầu phi chức năng

> Trạng thái: **Bản nháp chờ review**. Các con số là mục tiêu cho MVP với tải khoảng 500–5.000 đơn/ngày; mục có nhãn **[Giả định]** cần xác nhận.

## 1. Hiệu năng

| Chỉ số | Mục tiêu **[Giả định]** |
|---|---|
| p95 thời gian phản hồi API đọc (danh sách, chi tiết Sản phẩm, giỏ) | ≤ 300 ms |
| p95 `POST /store/checkout` (không tính thời gian gọi GHN) | ≤ 800 ms |
| Tải đỉnh khi có khuyến mãi | 50 request/giây vào API, 10 đơn/giây, không bán vượt Tồn kho |
| Thời gian từ IPN tới đơn chuyển `PLACED` | p95 ≤ 5 giây |
| Email gửi sau sự kiện | p95 ≤ 1 phút |

Cách đạt được:

- Không có N+1 query: `django-zeal` bật trong test, test fail nếu có.
- Danh sách Sản phẩm dùng `catalog_variant.is_available` (bản sao) để lọc "còn hàng" mà không phải join sang `inventory`.
- Cache trong Redis: cây danh mục (5 phút), báo giá GHN (10 phút), dữ liệu địa giới (1 ngày).
- Checkout khoá dòng `inventory_stock_item` theo thứ tự `variant_id` để tránh deadlock khi nhiều người mua cùng lúc.

## 2. Độ sẵn sàng và phục hồi

| Chỉ số | Mục tiêu **[Giả định]** |
|---|---|
| Độ sẵn sàng của API (production) | 99,5% / tháng |
| RPO (dữ liệu tối đa có thể mất) | ≤ 5 phút (RDS PITR) |
| RTO (thời gian khôi phục) | ≤ 1 giờ |
| Khi GHN lỗi | Vẫn checkout được (phí ship dự phòng) |
| Khi VNPay/MoMo lỗi | Vẫn đặt được đơn COD |
| Khi Redis lỗi | API đọc vẫn chạy (cache bỏ qua); sự kiện nằm chờ trong outbox |

## 3. Bảo mật

Xem [05-auth-security.md](./05-auth-security.md). Thêm:

- Không lưu dữ liệu thẻ (thuộc phạm vi của VNPay, MoMo).
- Mã hoá khi truyền (TLS 1.2+) và khi lưu (RDS, S3, ElastiCache bật encryption at rest).
- Rà soát lỗ hổng phụ thuộc trong mỗi lần chạy CI.

## 4. Quan sát hệ thống (observability)

| Loại | Công cụ | Nội dung |
|---|---|---|
| Log | `structlog` → stdout (JSON) → CloudWatch | Mỗi dòng có `request_id`, `user_id` (nếu có), `order_code` (nếu có); che PII |
| Lỗi | Sentry | API, Celery task, relay |
| Health | `/healthz`, `/readyz` | Dùng cho ALB và ECS health check |
| Chỉ số nghiệp vụ cần cảnh báo | Sentry / CloudWatch | Outbox tồn quá 1.000 sự kiện chưa gửi; Payment `pending` quá 30 phút; tỉ lệ đơn dùng phí ship dự phòng > 10%; số task Celery lỗi hết retry > 0 |

`request_id` lấy từ header `X-Request-ID` nếu có, ngược lại tự sinh; được đưa vào cả sự kiện outbox để lần theo một luồng từ API tới email.

## 5. Khả năng mở rộng

| Khi | Làm gì |
|---|---|
| API chậm do CPU | Tăng số task ECS của API |
| Queue Celery dài | Tăng worker; tách worker riêng cho queue `emails` / `integrations` |
| Tìm kiếm chậm hoặc cần tìm sai chính tả | Thêm Meilisearch (giai đoạn 2) |
| Cần phát lại sự kiện cho hệ thống mới, hoặc lưu lượng > 1.000 sự kiện/giây | Thêm adapter Kafka ([ADR 0007](../adr/0007-events-outbox-celery-no-kafka.md)) |
| Một module cần scale hoặc deploy độc lập | Tách module đó thành service; ranh giới `contracts.py` + sự kiện đã sẵn |

## 6. Chất lượng code

| Cổng chặn trong CI | Điều kiện để qua |
|---|---|
| `ruff check`, `ruff format --check` | Không lỗi |
| `mypy` | Không lỗi (`--strict` cho `services`, `selectors`, `contracts`) |
| `lint-imports` | Không vi phạm ranh giới module |
| `pytest` | Toàn bộ test qua |
| Độ phủ test | ≥ 80% cho `modules/*/services`, không đặt ngưỡng toàn repo ([12-testing-strategy.md](./12-testing-strategy.md) mục 8) |
| OpenAPI | Schema sinh ra trùng với `backend/openapi.yaml` đã commit |
| Migration | Không thiếu migration (`makemigrations --check`), không trùng số |
| Lỗ hổng phụ thuộc | Không có lỗ hổng mức cao |

## 7. Bản địa hoá

- Thời gian lưu UTC, hiển thị `Asia/Ho_Chi_Minh`.
- `error.message` và email dịch vi/en bằng `gettext`; mặc định `vi`.
- Nội dung Sản phẩm, danh mục chỉ tiếng Việt.
- Số tiền VND là số nguyên; định dạng hiển thị ("250.000 ₫") do Frontend lo.
