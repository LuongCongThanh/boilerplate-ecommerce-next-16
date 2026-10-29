# Phase 7 — done

1. Báo người dùng: URL PR, tiêu đề, trạng thái CI, từng AC → kết quả, việc chưa kiểm (AC `untestable`), ticket mới đã tạo. Nói thẳng phần nào chưa được kiểm chứng.
2. Hỏi bằng `AskUserQuestion`: merge ngay (khuyên dùng khi CI xanh và không còn mục mở), hay chờ (người dùng tự review hoặc merge sau).
3. Merge ngay:

   ```bash
   GH_TOKEN="$(gh auth token --user LuongCongThanh)" gh pr merge <số> --squash --delete-branch
   git switch dev && git pull
   python S/scripts/progress.py
   ```

   Chờ: ghi `next=chờ merge PR #<số>`. Lần chạy sau, `reference/resume.md` kiểm trạng thái PR.
4. `state.py transition <T> --to retro --next "retro skill" --reason "<merged / chờ merge>"`, rồi vào phase 8 ngay: retro cần phiên này còn trong context.

## Xong khi

Người dùng đã chọn merge hoặc chờ; đã merge thì ticket là `resolved` trên `origin/dev` và `progress.py` in ticket tiếp theo; `phase` là `retro`.
