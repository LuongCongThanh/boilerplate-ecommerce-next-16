# Roadmap MVP

Thứ tự làm backend cho MVP, theo các lát dọc: mỗi mốc chạy được từ đầu tới cuối và có test flow riêng, không làm xong từng module theo lớp rồi mới ghép. Mỗi mốc là một thư mục `.scratch/<slug>/` có `spec.md` và ticket ([issue-tracker](../../docs/agents/issue-tracker.md)). Chỉ M0 đã có spec; các mốc sau tạo spec khi mốc trước gần xong, để spec dựa trên code đã có.

## Notes

| Mốc | Thư mục | Nội dung | User story | Xong khi |
|---|---|---|---|---|
| **M0** | [`backend-bootstrap`](../backend-bootstrap/spec.md) | Khung Django, `shared` (BaseModel, events/outbox, idempotency, API cơ sở, địa giới), Docker Compose, CI, các cổng chặn | — | `make up`, `make lint`, `make test` xanh ở local và CI; test flow outbox (publish → relay → handler) qua |
| **M1** | `catalog-inventory` | identity lõi (Account, JWT login/refresh/logout cho cả hai nhánh, ADR 0002/0014), catalog (Danh mục, Sản phẩm, Biến thể, size, màu, ảnh, Giá khuyến mãi), inventory (StockItem, Nhập kho, điều chỉnh, Kiểm kê), storefront đọc và tìm kiếm | US-101 → 104, 701 → 703, 801 → 805 | Admin tạo được Sản phẩm, Staff nhập kho, storefront lọc/tìm đúng BR-CAT-13 |
| **M2** | `checkout-cod` | Giỏ hàng, Voucher, báo giá phí ship qua Fake GHN, Tính thử + `quote_token`, checkout COD, email "Đặt đơn thành công", cấu hình vận hành | US-201 → 204, 301 → 305, 307, 308, 901, 1002 | Test concurrency hai Người mua cùng mua Biến thể cuối cùng qua; flow COD tạo đơn `PLACED` và EmailLog |
| **M3** | `online-payment` | Thanh toán online qua Fake Gateway, IPN, khởi tạo có thể khôi phục (ADR 0013), Đối soát, T3/T4/T5, tiền về sai số tiền hoặc cho đơn không còn chờ thanh toán, Hoàn tiền `requested` | US-306, 403, 608 | Flow online thành công, hết hạn, trả hai lần, sai số tiền đều qua với Fake Gateway |
| **M4** | `order-fulfillment` | Back-office xử lý đơn T6 → T14, Bàn giao và Vận đơn qua Fake GHN, webhook GHN, Cờ cần xử lý, xác nhận nhập lại kho, Khách vãng lai tra cứu, lịch sử đơn | US-401, 402, 601 → 604, 607, 609, 1004 | Flow checkout → giao → Hoàn tất (T13) chạy hết bằng Fake provider |
| **M5** | `returns-refunds` | Đổi trả theo dòng, Hoàn tiền thủ công, báo cáo Doanh thu, xuất đơn đã thu tiền | US-605, 606, 1003 | Ví dụ làm tròn ở BR-RET-07 và BR-REV-01 thành test qua |
| **M6** | `identity-privacy` | Đăng ký (US-501 AC2 không lộ email), xác thực email, Google, quên mật khẩu, hồ sơ, sổ địa chỉ, gắn đơn vãng lai, quản lý Staff, Yêu cầu xoá dữ liệu (ADR 0016), log truy cập | US-501 → 506, 1001, 1101, 1102 | Flow ẩn danh hoàn tất chỉ khi mọi handler bắt buộc `completed`; không còn số điện thoại thô trong bằng chứng |
| **M7** | `sandbox-acceptance` | Nghiệm thu VNPay, MoMo, GHN sandbox qua tunnel ([06 mục 8](../../docs/architecture/06-integrations.md#8-nghiệm-thu-với-sandbox-thật-trước-khi-lên-aws)), test tải k6 (ticket [01](../sandbox-acceptance/issues/01-load-test-k6-staging.md)), danh sách go-live ([06-compliance mục 6](../../docs/business/06-compliance.md#6-điều-kiện-go-live)) | — | Mọi mục **[Cần xác minh]** đã gỡ hoặc có quyết định ghi lại |

M1 có identity lõi vì endpoint back-office của catalog và inventory cần xác thực Staff/Admin. Các luồng còn lại của identity để tới M6, vì checkout của Khách vãng lai không cần Tài khoản.

## Tiến độ

Cập nhật trong cùng PR đóng ticket. Nguồn sự thật vẫn là dòng `Status:` của từng ticket; bảng này chỉ để nhìn nhanh.

| Mốc / feature | Trạng thái | Ticket |
|---|---|---|
| [`dev-security-baseline`](../dev-security-baseline/spec.md) | Gần xong | ✅ 01, 02 · 🟡 03 chờ chủ repo tự kiểm tra 3 AC |
| **M0** [`backend-bootstrap`](../backend-bootstrap/spec.md) | Đang làm | ✅ 06, 07 · 🟡 08 script đã có, chưa chạy trên máy Windows thật · ⬜ 09 (làm tiếp theo) → 16 → 11, 17 · 09 → 12 · 07 + 08 → 15 → 14 · 09 + 15 → 10 → 18 · ⬜ 01–04 làm được · ⏸ 13 macOS, không chặn M0 |
| **M1** – **M6** | Chưa có spec | Tạo spec khi mốc trước gần xong |
| **M7** `sandbox-acceptance` | Chưa có spec | ⏸ [01](../sandbox-acceptance/issues/01-load-test-k6-staging.md) k6, `needs-triage` |

Ký hiệu: ✅ `resolved` · 🟡 đang dở · ⬜ chưa làm · ⏸ để sau.

## Decisions-so-far

- 29/10/2026: Tài liệu `docs/` chốt cho MVP; code tới đâu cập nhật tài liệu tới đó trong cùng PR ([README](../../README.md#trạng-thái-tài-liệu)).
- 29/10/2026: Python 3.14, bỏ `uuid-utils` ([ADR 0008](../../docs/adr/0008-uuid-v7-primary-keys.md)).
- 29/10/2026: Các con số nghiệp vụ trước đây là `[Giả định]` đã chốt; con số kỹ thuật mang nhãn `[Giả định · kiểm chứng: …]`.
- 29/10/2026: Đăng ký luôn trả `202` như nhau, không lộ email đã tồn tại (US-501 AC2).
- 29/10/2026: Bằng chứng tuân thủ giữ HMAC số điện thoại sau ẩn danh ([ADR 0016](../../docs/adr/0016-erasure-evidence-phone-hmac.md)).
- 29/10/2026: Hoá đơn điện tử giữ xuất thủ công ở MVP; kế toán xác nhận trước go-live.
- 29/10/2026: ADR 0019 đổi số thành [0015](../../docs/adr/0015-local-postgres-on-host.md).
- 29/10/2026: Không dùng Django Admin ở mọi môi trường, kể cả local; xem dữ liệu bằng `psql`/IDE ([ADR 0004](../../docs/adr/0004-custom-nextjs-admin.md)).
- 29/10/2026: Biến môi trường và lệnh `Makefile` thêm ở mốc dùng tới, không khai báo trước ([08](../../docs/architecture/08-local-development.md) mục 2.3 và 3).
- 29/10/2026: Compose có service `migrate` chạy trước các service app.
- 29/10/2026: Đóng [dev-security-baseline/02](../dev-security-baseline/issues/02-ci-and-dependabot.md); trivy và Dependabot cho `backend/` chuyển sang [backend-bootstrap/14](../backend-bootstrap/issues/14-trivy-and-dependabot-backend.md).
- 29/10/2026: Ticket k6 chuyển từ M0 sang [sandbox-acceptance/01](../sandbox-acceptance/issues/01-load-test-k6-staging.md) (M7).
- 29/10/2026: Làm ticket 07 song song với 08; phần cần container gọi PostgreSQL trên máy tách sang ticket 15.
- 29/10/2026: Tách ticket lớn của M0: 07 → 07 + 15 (Compose), `gen_importlinter.py` gộp vào 04; 09 → 09 + 16 (lớp API) + 17 (địa giới); 10 → 10 + 18 (lệnh vận hành).
- 29/10/2026: `sync_beat_schedule` làm ở ticket 15 vì service `migrate` gọi nó; service `relay` thêm vào Compose ở ticket 10 cùng `run_outbox_relay`.

## Fog

Các mục phụ thuộc bên ngoài, gắn vào mốc cần chúng. Không mục nào chặn M0.

| Mục | Nguồn | Mốc cần |
|---|---|---|
| Container gọi được PostgreSQL trên host: Windows (WSL `networkingMode=mirrored`) | [08](../../docs/architecture/08-local-development.md), ticket [08](../backend-bootstrap/issues/08-local-postgres-installer.md) | M0 |
| Container gọi được PostgreSQL trên host: macOS | [08](../../docs/architecture/08-local-development.md), ticket [13](../backend-bootstrap/issues/13-local-postgres-installer-macos.md) | Khi có người dùng Mac, không chặn mốc nào |
| Tham số, mã kết quả, chữ ký hiện hành của VNPay và MoMo | [06 mục 2–3](../../docs/architecture/06-integrations.md) | M3 (Fake theo tài liệu), M7 (sandbox) |
| GHN: địa chỉ 2 cấp, cơ chế xác thực webhook, chống trùng `client_order_code` | [06 mục 4](../../docs/architecture/06-integrations.md#4-ghn), [04 mục 4.3](../../docs/architecture/04-api-contract.md#43-webhook-apiv1webhooks) | M4 (Fake), M7 (sandbox); US-1004 bỏ được nếu GHN đã dùng 2 cấp |
| Cổng thanh toán có yêu cầu IP server cố định | [09](../../docs/architecture/09-deployment-aws-target.md) | Trước khi lên AWS |
| Pháp lý: dữ liệu cá nhân, hoá đơn điện tử, thông báo Bộ Công Thương, thời hạn lưu payload | [06-compliance](../../docs/business/06-compliance.md#6-điều-kiện-go-live) | Go-live |
