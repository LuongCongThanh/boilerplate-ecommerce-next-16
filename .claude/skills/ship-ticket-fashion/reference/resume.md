# Làm tiếp

Đọc khi `state.py start` in `READ …/reference/resume.md`: có cờ, có slice đang mở, hoặc phase không chỉ đơn giản tiếp tục từ `next`.

## Cờ trước, trước mọi việc

- `BRANCH RED` (nhánh hiện tại khác `branch` của state) → hỏi người dùng: chuyển sang nhánh của state (khuyên dùng), hay lấy nhánh hiện tại làm `branch` mới.
- `DIRTY` → xem `git status --short`: file của ticket thì làm tiếp; file của việc khác thì hỏi người dùng giữ hay stash.
- `BEHIND origin/dev` → `git fetch origin && git rebase origin/dev` trước phase 6; ở phase sớm hơn thì rebase khi tiện, chạy lại test sau rebase.
- `SLICE OPEN` → `ListAgents` trước khi tạo agent mới; agent đang chạy trên slice đó giữ slice tới khi trả về.
- `NO PR` ở phase `done` → PR chưa mở được: quay lại phase 6 bước mở PR.

## Theo phase

| Phase | Làm tiếp |
| --- | --- |
| `grill` | G1 đã hỏi nhưng chưa trả lời → trình lại G1 từ `## Quyết định` trong `spec.md` và slice trong state |
| `sync` | G2 đã hỏi nhưng chưa trả lời → trình lại G2; các phase trước giữ nguyên |
| `done` | `gh pr view <pr> --json state` (tài khoản ở `phases/6-ship.md`): `MERGED` → bước sau merge của phase 7; `OPEN` → hỏi merge hay chờ |
| `retro` | Danh sách đề xuất đã trình nhưng chưa trả lời → trình lại; đã ghi xong → bước push của phase 8 |
| `closed` | Ticket đã xong: chạy `progress.py`, đề xuất ticket tiếp theo |
