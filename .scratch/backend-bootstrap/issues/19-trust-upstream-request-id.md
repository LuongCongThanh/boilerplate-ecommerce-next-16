# Dùng `X-Request-ID` từ BFF làm `request_id`

Status: ready-for-agent

Blocked by: 16

Spec: [spec.md](../spec.md)

Tách từ ticket [16](./16-shared-api-layer.md) khi grilling ngày 29/10/2026.

## Bối cảnh

[10-nfr](../../../docs/architecture/10-nfr.md) ghi `request_id` lấy từ `X-Request-ID` nếu có, không có thì tự sinh. Hiện `django-structlog` luôn tự sinh vì `DJANGO_STRUCTLOG_TRUST_UPSTREAM_REQUEST_ID` mặc định `False`. Bật cờ đó thì client bất kỳ cũng đặt được `request_id`; nên chỉ tin header khi `X-BFF-Secret` khớp (middleware `client_ip` của ticket 16).

## Việc cần làm

- Chọn cách tin `X-Request-ID` chỉ khi secret BFF đúng, kiểm định dạng và độ dài.
- Trả `X-Request-ID` trong response nếu tài liệu yêu cầu.

## Acceptance criteria

- [ ] Secret BFF đúng và `X-Request-ID` hợp lệ thì `error.request_id` và log dùng giá trị đó.
- [ ] Thiếu hoặc sai secret thì `request_id` được tự sinh, bỏ qua header.
