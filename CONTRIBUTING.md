# Hướng dẫn đóng góp

Đọc theo thứ tự:

1. [GLOSSARY.md](./GLOSSARY.md): thuật ngữ dùng chung trong code và tài liệu.
2. [Môi trường phát triển local](./docs/architecture/08-local-development.md): cài đặt trên macOS hoặc Windows.
3. [Cấu trúc Backend](./docs/architecture/02-backend-structure.md): module, quy tắc từng file, ranh giới giữa các module.
4. [Quy ước Git](./docs/architecture/11-git-workflow.md): nhánh, commit, PR, release.

## Tóm tắt quy trình

```bash
git switch dev && git pull
git switch -c feat/<mo-ta-ngan>
# code + test
make lint && make test
git push -u origin feat/<mo-ta-ngan>
# mở PR vào dev, tiêu đề theo Conventional Commits
```

| Quy tắc | Chi tiết |
|---|---|
| Nhánh chính | `main` (production) ← `uat` (nghiệm thu, triển khai lên staging) ← `dev` (tích hợp) ← nhánh tính năng |
| Commit, tên nhánh, tiêu đề PR | Tiếng Anh, theo Conventional Commits: `feat(ordering): add COD checkout` |
| Merge vào `dev` | Squash merge |
| Merge `dev` → `uat` và `uat` → `main` | Merge commit (không squash) |
| Push thẳng vào `dev` | Chỉ khi thay đổi nhỏ, gấp và đã chạy `make lint`, `make test` |
| Push thẳng vào `uat` hoặc `main` | Không được |
| Force-push | Chỉ trên nhánh tính năng của mình, không bao giờ trên `dev`, `uat` hoặc `main` |

## Quy ước code

Chi tiết ở [Cấu trúc Backend §9](./docs/architecture/02-backend-structure.md#9-quy-ước-code). Tóm tắt:

- Tên trong code bằng tiếng Anh; comment và docstring bằng tiếng Việt.
- Hàm service đặt tên `<verb>_<noun>` (`place_order`); selector dùng `get_` / `find_` / `list_`.
- Format bằng `ruff format` (dòng tối đa 100 ký tự), lint bằng `ruff check` + `mypy` + `lint-imports`. Chạy `make fmt` trước khi commit.
- Docstring Google style, bắt buộc cho hàm public trong `contracts.py` và `services/`.
- Model kế thừa `shared.models.BaseModel` (khoá chính UUID v7), không tự khai báo `id`.
- Test: dữ liệu tạo bằng `factory-boy`, không mock ORM, chỉ giả lập hệ thống bên ngoài. Branch coverage của `services/` và `handlers.py` tối thiểu 80%, tính riêng từng module.
- Log bằng `structlog.get_logger(__name__)`, message là tên sự kiện `snake_case` kèm keyword, không f-string. Không log PII, token hay payload thanh toán.

## Bảo mật khi dùng AI agent

- `.claude/settings.json` có rule `deny` chặn Claude Code đọc `.env*` (trừ `.env.example`), `.secrets/` và `*.pem`. Không xoá hoặc ghi đè các rule này trong `settings.local.json`.
- Mở Claude Code từ **gốc repo**. Rule chỉ áp dụng cho thư mục đang mở và các thư mục con, nên mở từ `docs/` thì `.env` ở gốc repo không được bảo vệ.
- Rule không chặn được script tự đọc file (ví dụ một script Python mở `.env`). Đừng chạy lệnh do agent đề xuất nếu lệnh đó in nội dung secret.
- Không dán secret, token hoặc dữ liệu khách hàng thật vào prompt.

## Khi nào cần cập nhật tài liệu

Tài liệu đã chốt cho MVP; code chạm tới phần nào thì sửa tài liệu phần đó **trong cùng PR** ([quy ước](./README.md#trạng-thái-tài-liệu)).

- Thêm hoặc đổi thuật ngữ nghiệp vụ → `GLOSSARY.md`.
- Đổi quy tắc nghiệp vụ → `docs/business/04-business-rules.md` (giữ mã `BR-xxx`).
- Quyết định khó đảo ngược, có đánh đổi thật → thêm ADR mới trong `docs/adr/`.
- Thêm endpoint → OpenAPI tự sinh; chỉ cập nhật `docs/architecture/04-api-contract.md` nếu đổi quy ước chung.
