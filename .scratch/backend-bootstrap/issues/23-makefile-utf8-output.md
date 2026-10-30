# `make lint` lỗi mã hoá trên Windows khi output bị chuyển hướng

Status: needs-triage

Spec: [spec.md](../spec.md)

Tách từ retro của ticket [17](./17-shared-geo.md) ngày 30/10/2026.

## Bối cảnh

Trên Windows, Python ghi stdout bị chuyển hướng (pipe, file) bằng code page `cp1252`. `lint-imports` in tên contract tiếng Việt nên dừng với `UnicodeEncodeError: 'charmap' codec can't encode character 'ứ'` và exit 1, dù các contract đều giữ. Tái hiện trong `backend/`, không đặt `PYTHONIOENCODING` hay `PYTHONUTF8`: `uv run lint-imports > out.txt`. Gặp khi agent, IDE task hoặc script chạy `make lint` và đọc output. CI chạy Linux nên không gặp; `run_logged.py` của skill đặt `PYTHONIOENCODING=utf-8` nên cũng không gặp.

## Việc cần làm

- `backend/Makefile` đặt `export PYTHONUTF8 := 1` (cú pháp của make, hợp quy tắc recipe ở ADR 0017) để mọi recipe chạy Python ở chế độ UTF-8.
- Ghi vào `docs/architecture/08-local-development.md` nếu mục lệnh `make` cần nhắc.

## Acceptance criteria

- [ ] Trên Windows, `make lint > out.txt` exit 0 khi code sạch, không đặt biến môi trường nào trước.
- [ ] `make lint` và `make test` trên CI vẫn xanh.
