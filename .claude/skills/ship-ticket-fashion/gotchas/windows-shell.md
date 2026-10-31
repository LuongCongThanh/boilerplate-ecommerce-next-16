# Gotchas: shell trên Windows

- **`gh pr create -F <file>` báo "flag needs an argument"**: nguyên nhân: đường dẫn scratchpad (`C:/Users/SMD415~2/…`, tên user có dấu cách) bị xuống dòng hoặc tách khi dán lệnh. Sửa: ghi thân PR vào `.git/PR_BODY.md` rồi `-F .git/PR_BODY.md`. (PR #12)
- **Tham số bắt đầu bằng `/` thành `C:/Program Files/Git/...`**: nguyên nhân: Git Bash tự đổi đường dẫn. Sửa: thêm `MSYS_NO_PATHCONV=1` trước lệnh. (dự án saafehouse-fe)
- **`Get-Content` của PowerShell lỗi với đường dẫn có `[` `]`**: nguyên nhân: `[ ]` là wildcard. Sửa: `-LiteralPath`, hoặc dùng Bash tool. (dự án saafehouse-fe)
- **`UnicodeEncodeError`/`UnicodeDecodeError` khi Python in tiếng Việt ra pipe** (`python -c … | …`, test gọi `subprocess.run(..., text=True)` tới `manage.py`): nguyên nhân: output bị chuyển hướng ghi bằng `cp1252`. Sửa: đặt `PYTHONUTF8=1` trước lệnh, hoặc trong `env` của subprocess. (backend-bootstrap/21)
- **File LF thành CRLF sau khi script sửa** (git cảnh báo "CRLF will be replaced by LF"): nguyên nhân: `pathlib.Path.write_text` đổi `\n` thành `\r\n` trên Windows. Sửa: dùng Edit tool, hoặc `write_text(..., newline="\n")`. (backend-bootstrap/21)
