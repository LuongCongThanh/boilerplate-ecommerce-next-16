# Commit message

```
<type>(<scope>): <mô tả tiếng Anh, thì hiện tại, chữ đầu viết thường, không dấu chấm cuối>

<Thân: VÌ SAO, và phần chưa làm hoặc còn gap của commit này nếu có.>

Refs: .scratch/<feature>/issues/NN-<slug>.md
```

- `type`, `scope`: `docs/architecture/11-git-workflow.md` mục 3. Hook `commitizen` chặn sai định dạng.
- Commit của slice: `feat` / `fix` / `refactor` / `test` theo việc slice làm. Commit chỉ đổi ticket hoặc tài liệu: `docs: …`.
- Đổi API hoặc contract sự kiện: thêm `!` sau scope và dòng `BREAKING CHANGE:` trong footer.

Ví dụ: `feat(shared): return ErrorDTO for unhandled API errors`
