# Báo cáo

### Báo cáo 30/10/2026

**Nhánh:** `feat/identity-account` · **PR:** #42 · **Mode:** full

#### Đã làm

| AC | Bằng chứng |
| --- | --- |
| 1. `make migrate` tạo `identity_account` trong `modules/0001` | `modules/identity/tests/test_models_account.py::test_initial_migration_creates_identity_account` |
| 2. Hai email chỉ khác hoa thường không tạo được hai Tài khoản | `modules/identity/tests/test_models_account.py::test_email_unique_ignores_case` (DB `UNIQUE(lower(email))`); thêm `::test_manager_normalizes_email_to_lowercase`, `test_services_accounts.py::test_create_staff_account_rejects_email_used_ignoring_case` |
| 3. `create_staff --admin` tạo `kind = admin`; chạy lại cùng email báo lỗi rõ | `modules/identity/tests/test_commands_create_staff.py::test_create_staff_admin_creates_admin_account`, `::test_create_staff_same_email_raises_command_error`; đầu vào sai: `::test_create_staff_rejects_weak_password`, `::test_create_staff_rejects_blank_email`, `::test_create_staff_rejects_mismatched_password`; service: `test_services_accounts.py::test_create_staff_account_rejects_invalid_email`, `::test_create_staff_account_rejects_weak_password`, `::test_create_staff_account_reraises_other_integrity_error` |
| 4. Không có bảng group/permission; không có `django.contrib.admin` ở mọi môi trường | `modules/identity/tests/test_models_account.py::test_no_django_auth_tables_after_migrate`, `::test_django_admin_not_installed_in_any_settings` |
| Quyết định *Fixture* | `modules/identity/tests/test_api_backoffice_clients.py::test_staff_client_passes_is_staff`, `::test_admin_client_passes_is_admin`, `::test_staff_client_denied_by_is_admin` |

Ràng buộc khác của 03 §2.1: `::test_anonymized_account_must_be_inactive`, `::test_unknown_kind_rejected_by_db`, `::test_unknown_language_rejected_by_db`. Service: `test_services_accounts.py::test_create_staff_account_stores_lowercase_email`, `::test_create_staff_account_rejects_customer_kind`.

`make lint` xanh (ruff, format, mypy, import-linter 1 contract kept) · `make test`: 294 passed trong 9.79s

#### Chưa làm

- Hai lệnh cùng email chạy song song chưa có test concurrency; nhánh đổi `IntegrityError` của `identity_account_email_lower_uniq` thành `EmailAlreadyUsed` được phủ bằng test email trùng, nhánh ném lại vi phạm khác có `::test_create_staff_account_reraises_other_integrity_error`.

#### Gap

- `kind = customer` làm `create_staff_account` ném `ValueError` (lỗi của bên gọi), không phải `DomainError`.
- `UserAttributeSimilarityValidator` so với `email`, `full_name` vì Account không có `username`, `first_name`.
- Fixture `admin_client` ghi đè fixture cùng tên của pytest-django (vốn cần `django.contrib.auth` nên không chạy được ở repo này). Fixture chỉ trả `APIClient`.
- Backlog: `get_by_natural_key` khớp email phân biệt hoa thường (M1 đăng nhập); `--full-name` dài hơn 255 ký tự ném `DataError` (M6).

#### Thay đổi theo yêu cầu

- `shared/tests/test_migrations.py`: khối `finally` của `test_reverse_drops_function_but_keeps_extensions` chạy `migrate` mọi app, vì `migrate shared zero` gỡ cả `modules.0001` (người dùng duyệt trong phase code, gộp vào S1).

#### Review

| Mã | Chỗ | Kết luận | Lý do |
| --- | --- | --- | --- |
| P1, B1 | `services/accounts.py`, `create_staff.py` | đã sửa | Email rỗng, sai định dạng, quá 254 ký tự tạo được Admin → `InvalidEmail` |
| T2, B4 | `services/accounts.py`, `create_staff.py` | đã sửa | `validate_password` chuyển vào service (`WeakPassword`); lệnh không dựng candidate nữa |
| B2, B5 | `services/accounts.py` | đã sửa | Bỏ truy vấn `iexact`; chỉ đổi `IntegrityError` của `identity_account_email_lower_uniq`, lỗi khác ném lại |
| T1, P4, P2, B9 | `test_commands_create_staff.py`, `create_staff.py` | đã sửa | Test log qua `json_logging` (12 §4); `account_id` là chuỗi UUID |
| B7, T5 | `test_models_account.py` | đã sửa | Đọc `INSTALLED_APPS` bằng `ast`, không import settings (tránh `structlog.configure` toàn cục); so với tập file cụ thể |
| P3 | `test_models_account.py` | đã sửa | Lọc thêm bảng chứa `group`/`permission` |
| B8 | `tests/factories.py` | đã sửa | `factory.django.Password` thay hook tự viết |
| T4 | `test_api_backoffice_clients.py` | đã sửa | Đổi tên theo `test_<tầng>_<chủ đề>.py` (02 §9.2) |
| B3 | `models/account.py` | chỉ báo | `get_by_natural_key` phân biệt hoa thường → backlog M1 |
| P5 | `services/accounts.py` | chỉ báo | `ValueError` cho `kind=customer` có chủ ý |
| B6, T3 | `services/accounts.py`, `models/__init__.py` | chỉ báo | Hash trước khi lưu và export `AccountManager`: vô hại |

#### Commit

| Task | Phase | AC | Commit | File |
| --- | --- | --- | --- | --- |
| plan | 1 grill | — | `86c0c21` docs: plan account bootstrap ticket | 1 |
| S1 | 2 code | 1, 2, 4 | `271d026` feat(identity): add Account custom user model in first modules migration | 11 |
| S2 | 2 code | 3 | `bcd584e` feat(identity): add create_staff command and staff account service | 10 |
| S3 | 2 code |  | `ccfba44` test(identity): add staff_client and admin_client fixtures | 2 |
| R1 | 4 review | — | `f2a9429` fix(identity): address review findings on staff account creation | 8 |

#### Tài liệu đã cập nhật

- `docs/architecture/02-backend-structure.md`: cây `conftest.py` ghi `staff_client`/`admin_client` dùng `force_authenticate` với `aud = backoffice` tới M1; bảng `services/` của identity thêm `create_staff_account`.
- `docs/architecture/12-testing-strategy.md` §4: cách `staff_client`/`admin_client` xác thực tới khi có JWT; `customer_client` ở M6.
- `docs/architecture/08-local-development.md` §2.4 bước 5: `make create-admin` hỏi email, nhập mật khẩu hai lần, tối thiểu 8 ký tự.
- `.scratch/backlog.md`: `get_by_natural_key` phân biệt hoa thường (M1), `--full-name` quá 255 ký tự (M6).
