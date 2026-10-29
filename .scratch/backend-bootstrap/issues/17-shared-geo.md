# Địa giới hành chính: Tỉnh/thành, Phường/xã, `load_geo` và endpoint

Status: ready-for-agent

Blocked by: 16

Spec: [spec.md](../spec.md)

Tách từ ticket [09](./09-shared-core.md).

## Việc cần làm

- `shared/geo/`: model `Province`, `Ward` (mã chính thức làm PK).
- Lệnh `load_geo` nạp dữ liệu từ `vietnam-provinces`, chạy lại an toàn. Thêm target `make load-geo` vào `Makefile`.
- Endpoint `GET store/geo/provinces` và `geo/provinces/{code}/wards`.

## Acceptance criteria

- [ ] `make load-geo` chạy hai lần liên tiếp không lỗi, không trùng dữ liệu.
- [ ] Endpoint địa giới trả array không phân trang.
- [ ] Mã tỉnh không tồn tại trả 404 dạng `ErrorDTO`.
