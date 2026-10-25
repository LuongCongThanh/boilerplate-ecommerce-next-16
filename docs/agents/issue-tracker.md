# Issue tracker: Markdown trong repo

Spec và ticket của repo này là file Markdown trong `.scratch/`, được commit lên git như tài liệu thường.

## Quy ước

- Mỗi feature một thư mục: `.scratch/<feature-slug>/`
- Spec nằm ở `.scratch/<feature-slug>/spec.md`
- Mỗi ticket là một file `.scratch/<feature-slug>/issues/<NN>-<slug>.md`, đánh số từ `01`. Không gộp nhiều ticket vào một file.
- Trạng thái ghi ở dòng `Status:` gần đầu file (xem `triage-labels.md`).
- Trao đổi và bình luận ghi nối vào cuối file, dưới heading `## Comments`.

## Ngôn ngữ

- Nội dung spec và ticket viết tiếng Việt; từ khoá kỹ thuật và tên trong code giữ tiếng Anh.
- Tên thư mục và tên file viết tiếng Anh, chữ thường, nối bằng `-`, ví dụ `checkout-cod/issues/02-reserve-stock.md`.

## Liên kết với nhánh và PR

- Tên nhánh không chứa mã ticket, ví dụ `feat/checkout-cod`.
- Mô tả PR ghi đường dẫn ticket ở dòng **Closes**, ví dụ `.scratch/checkout-cod/issues/02-reserve-stock.md`.

## Đóng ticket

Làm ngay trong PR của ticket đó, để ticket được merge vào `dev` cùng lúc với code:

1. Đổi thành `Status: resolved`.
2. Tick hết các acceptance criteria.
3. Thêm dòng `**PR:** #<số>`.

`resolved` là trạng thái đóng, không thuộc 5 trạng thái triage.

## Khi skill nói "publish to the issue tracker"

Tạo file mới trong `.scratch/<feature-slug>/`; tạo thư mục nếu chưa có.

## Khi skill nói "fetch the relevant ticket"

Đọc file theo đường dẫn được đưa. Thường người dùng sẽ đưa đường dẫn hoặc số ticket.

## Wayfinding (dùng cho `/wayfinder`)

**Map** là một file, mỗi ticket con là một file riêng.

- **Map**: `.scratch/<effort>/map.md`, gồm các phần Notes / Decisions-so-far / Fog.
- **Ticket con**: `.scratch/<effort>/issues/NN-<slug>.md`, đánh số từ `01`, câu hỏi nằm trong thân file. Dòng `Type:` ghi loại ticket (`research`/`prototype`/`grilling`/`task`); dòng `Status:` ghi `claimed`/`resolved`.
- **Chặn nhau**: dòng `Blocked by: NN, NN` gần đầu file. Ticket hết bị chặn khi mọi file nó liệt kê đều `resolved`.
- **Frontier**: quét `.scratch/<effort>/issues/` tìm file còn mở, không bị chặn và chưa ai nhận; số nhỏ nhất được làm trước.
- **Nhận việc**: đặt `Status: claimed` và lưu file trước khi bắt đầu.
- **Giải quyết**: ghi câu trả lời dưới heading `## Answer`, đặt `Status: resolved`, rồi thêm một dòng tóm tắt kèm đường dẫn vào phần Decisions-so-far của `map.md`.
