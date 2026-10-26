# Trạng thái triage

Các skill dùng 5 vai trò triage chuẩn. File này ánh xạ từng vai trò sang chuỗi thực tế ghi ở dòng `Status:` của ticket trong repo.

| Nhãn trong mattpocock/skills | Nhãn trong repo     | Ý nghĩa                                              |
| ---------------------------- | ------------------- | ---------------------------------------------------- |
| `needs-triage`               | `needs-triage`      | Mới ghi lại, người phụ trách cần đánh giá            |
| `needs-info`                 | `needs-info`        | Thiếu thông tin, đang chờ người báo trả lời          |
| `ready-for-agent`            | `ready-for-agent`   | Đặc tả đủ rõ để agent tự làm mà không cần hỏi lại   |
| `ready-for-human`            | `ready-for-human`   | Cần người làm                                        |
| `wontfix`                    | `wontfix`           | Quyết định không làm                                 |

Khi skill nhắc tới một vai trò (ví dụ "apply the AFK-ready triage label"), dùng chuỗi tương ứng ở cột "Nhãn trong repo".

`resolved` là trạng thái đóng ticket, không thuộc bảng trên. Xem `issue-tracker.md` mục "Đóng ticket".
