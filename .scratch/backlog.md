# Backlog

Việc tốt nhưng ngoài phạm vi ticket, phát hiện khi làm hoặc review. Mỗi việc một dòng: `DD/MM/YYYY · <ticket nguồn> · <việc> · <mốc nên xem lại>`. Việc chặn mốc đang làm hoặc mốc kế tiếp thì thành ticket `needs-triage` và xoá dòng ở đây ([quy tắc](../.claude/skills/ship-ticket-fashion/reference/rules.md)).

- 30/10/2026 · backend-bootstrap/11 · Lease `Idempotency-Key` 60 giây không gia hạn khi tác động chạy lâu · M2 checkout
- 30/10/2026 · backend-bootstrap/11 · `claim` chờ khoá dòng thay vì trả 202 ngay khi worker kia đang commit · M2 checkout
- 30/10/2026 · backend-bootstrap/11 · `scope` vượt `varchar(255)` khi path dài hơn ~175 ký tự → 500 · M3 Thanh toán
- 30/10/2026 · backend-bootstrap/11 · Key `in_progress`, `resource_id` NULL, bị bỏ lại khi worker chết không bao giờ purge (03 §1.5, 07 §3.2 chỉ cho xoá `completed`) · trước go-live
