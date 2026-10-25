# Hướng dẫn đóng góp

Đọc theo thứ tự:

1. [GLOSSARY.md](./GLOSSARY.md): thuật ngữ dùng chung trong code và tài liệu.
2. [Môi trường phát triển local](./docs/architecture/08-local-development.md): cài đặt trên macOS hoặc Windows (WSL2).
3. [Cấu trúc Backend](./docs/architecture/02-backend-structure.md): module, quy tắc từng file, ranh giới giữa các module.
4. [Quy ước Git](./docs/architecture/11-git-workflow.md): nhánh, commit, PR, release.

## Tóm tắt quy trình

```bash
git switch dev && git pull
git switch -c feat/<ticket>-<mo-ta-ngan>
# code + test
make lint && make test
git push -u origin feat/<ticket>-<mo-ta-ngan>
# mở PR vào dev, tiêu đề theo Conventional Commits
```

| Quy tắc | Chi tiết |
|---|---|
| Nhánh chính | `main` (production) ← `dev` (staging) ← nhánh tính năng |
| Commit, tên nhánh, tiêu đề PR | Tiếng Anh, theo Conventional Commits: `feat(ordering): add COD checkout` |
| Merge vào `dev` | Squash merge |
| Merge `dev` → `main` | Merge commit (không squash) |
| Push thẳng vào `dev` | Chỉ khi thay đổi nhỏ, gấp và đã chạy `make lint`, `make test` |
| Push thẳng vào `main` | Không được |
| Force-push | Chỉ trên nhánh tính năng của mình, không bao giờ trên `dev` hoặc `main` |

## Khi nào cần cập nhật tài liệu

- Thêm hoặc đổi thuật ngữ nghiệp vụ → `GLOSSARY.md`.
- Đổi quy tắc nghiệp vụ → `docs/business/04-business-rules.md` (giữ mã `BR-xxx`).
- Quyết định khó đảo ngược, có đánh đổi thật → thêm ADR mới trong `docs/adr/`.
- Thêm endpoint → OpenAPI tự sinh; chỉ cập nhật `docs/architecture/04-api-contract.md` nếu đổi quy ước chung.
