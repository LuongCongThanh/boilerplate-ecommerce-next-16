# Gotchas: shell trên Windows

- **`gh pr create -F <file>` báo "flag needs an argument"**: nguyên nhân: đường dẫn scratchpad (`C:/Users/SMD415~2/…`, tên user có dấu cách) bị xuống dòng hoặc tách khi dán lệnh. Sửa: ghi thân PR vào `.git/PR_BODY.md` rồi `-F .git/PR_BODY.md`. (PR #12)
- **Tham số bắt đầu bằng `/` thành `C:/Program Files/Git/...`**: nguyên nhân: Git Bash tự đổi đường dẫn. Sửa: thêm `MSYS_NO_PATHCONV=1` trước lệnh. (dự án saafehouse-fe)
- **`Get-Content` của PowerShell lỗi với đường dẫn có `[` `]`**: nguyên nhân: `[ ]` là wildcard. Sửa: `-LiteralPath`, hoặc dùng Bash tool. (dự án saafehouse-fe)
