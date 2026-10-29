# Phase 6 — ship

Quy ước gốc: `docs/architecture/11-git-workflow.md`. File này chỉ ghi phần riêng của máy và repo này. G2 đã duyệt nên phase này không hỏi lại, trừ dòng `FAIL` của `check_ship.py`.

## Tài khoản `gh`

Máy có nhiều tài khoản GitHub. Mọi lệnh `gh` chạy qua Bash tool với tiền tố:

```bash
GH_TOKEN="$(gh auth token --user LuongCongThanh)" gh …
```

Repo `LuongCongThanh/fashion-store-backend`; remote `origin` dùng SSH alias `github-thanh`.

## 1. Push

```bash
git fetch origin && git rebase origin/dev
python S/scripts/run_logged.py --label test --cwd backend -- make test   # chỉ khi rebase kéo về commit mới
git push -u origin <nhánh>        # nhánh của mình: --force-with-lease sau rebase
```

## 2. Mở PR

1. Tiêu đề Conventional Commits, scope là module (`shared`, `catalog`…); tiêu đề này thành commit squash trên `dev`.
2. Thân PR theo `.github/pull_request_template.md`, ghi vào `.git/PR_BODY.md` (lý do ở `gotchas/windows-shell.md`). **Closes** là đường dẫn ticket; **Notes** là báo cáo trong ticket (Đã làm / Chưa làm / Gap, kết luận review); checklist tick theo sự thật, mục không áp dụng ghi N/A.
3. Tạo, rồi ghi số PR vào state:

```bash
GH_TOKEN="$(gh auth token --user LuongCongThanh)" gh pr create -B dev -H <nhánh> -t "<tiêu đề>" -F .git/PR_BODY.md --assignee @me
python S/scripts/state.py set <T> pr=<số>
```

## 3. Đóng ticket trong PR

```bash
python S/scripts/close_ticket.py <đường dẫn ticket> --pr <số>
python S/scripts/progress.py --feature <feature>
```

`close_ticket.py` in các AC vừa tick: đối chiếu với bảng AC → bằng chứng. AC nằm trong `untestable` (đọc từ state) không được tick và in riêng: đã kiểm tay thì tự tick, chưa thì ghi vào Notes của PR.

Cùng commit, sửa `.scratch/mvp-roadmap/map.md`: dòng của mốc trong bảng **Tiến độ** khớp `progress.py`; **Decisions-so-far** thêm `DD/MM/YYYY: …` cho mỗi quyết định ảnh hưởng ngoài ticket.

Commit `docs: close <chủ đề> ticket`, push.

## 4. CI

```bash
GH_TOKEN="$(gh auth token --user LuongCongThanh)" gh pr checks <số> --watch
```

Đỏ → `gh run view <id> --log-failed > .git/ship-ticket-fashion/logs/ci.log`, đọc đoạn lỗi, sửa trong phạm vi ticket, push. Đỏ ngoài phạm vi → *Cần người dùng*.

Check SonarCloud xanh cả khi còn issue (Quality Gate vẫn passed), nên đọc thêm comment của bot:

```bash
GH_TOKEN="$(gh auth token --user LuongCongThanh)" gh pr view <số> --json comments --jq '.comments[] | select(.author.login=="sonarqubecloud") | .body' | grep -oE '[0-9]+ (New issues?|Security Hotspots?)'
```

Số khác 0 → nhờ người dùng dán danh sách issue từ link dashboard trong comment, xử lý từng issue như finding *sửa* của phase 4 và ghi vào *Thay đổi theo yêu cầu* của báo cáo.

Mỗi lần push thêm vào PR đã mở: cập nhật thân PR (`gh pr edit <số> -F .git/PR_BODY.md`) và thêm comment tóm tắt đã sửa gì (`gh pr comment <số> -F <file>`).

## 5. Chuyển phase

`state.py transition <T> --to done --next "hỏi merge" --reason "PR #<số> mở, CI xanh"`.

## Xong khi

PR mở vào `dev`, số PR nằm trong state; ticket `resolved` với `**PR:**` trong PR; `map.md` khớp `progress.py`; CI xanh; SonarCloud 0 New issues và 0 Security Hotspots; `phase` là `done`.
