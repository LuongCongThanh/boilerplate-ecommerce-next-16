# Model `Account` trong migration đầu tiên và lệnh `create_staff`

Status: resolved

**PR:** #42

Blocked by: 09

Spec: [spec.md](../spec.md)

## Việc cần làm

- `modules/identity/models/account.py`: `Account` kế thừa `AbstractBaseUser` và `BaseModel`, không kế thừa `PermissionsMixin`, đủ cột và ràng buộc ở [03 mục 2.1](../../../docs/architecture/03-data-model.md#21-identity_account-tài-khoản). `AUTH_USER_MODEL = "modules.Account"`; đây là migration đầu tiên của `modules/migrations/`.
- `modules/models.py` import model của identity; `Meta.db_table = "identity_account"`.
- Lệnh `manage.py create_staff [--admin]` tạo Tài khoản `staff` hoặc `admin` (thêm target `make create-admin` vào `Makefile`); email trùng (không phân biệt hoa thường) với bất kỳ Tài khoản nào thì từ chối (US-1001 AC2, AC3).
- `modules/identity/tests/factories.py` cho Account; fixture `staff_client`, `admin_client` ở `backend/conftest.py` để trống phần xác thực, sẽ hoàn thiện khi có JWT ở M1.
- Hash mật khẩu tạm dùng mặc định của Django; Argon2 thêm ở M1 cùng luồng đăng nhập.

## Quyết định

Chốt khi grilling ngày 30/10/2026.

| Chủ đề | Quyết định |
|---|---|
| Tài liệu chi phối | `modules/identity/models/account.py`, `models/__init__.py`, `constants.py`, `modules/models.py`, `modules/migrations/0001_initial.py`: 03 §0.1–0.4 (BaseModel, kiểu, enum kèm `CHECK`, độ dài), 03 §0.9, 03 §2.1, 02 §5 (cây `modules/`), 02 §6 (khuôn module), 02 §7.1, 02 §9.2 (tên bảng, tên constraint), ADR 0006, ADR 0008. `config/settings/base.py` (`AUTH_USER_MODEL`, `AUTH_PASSWORD_VALIDATORS`): 03 §2.1, 05 §3 (độ mạnh mật khẩu). `modules/identity/services/accounts.py`, `exceptions.py`: 02 §6, 02 §9.1 (*Transaction*), §9.2 (tên service, lỗi nghiệp vụ), 04 §3 (`http_status`), 05 §2.3 (một email một Tài khoản), US-1001 AC2. `modules/management/commands/create_staff.py`: 02 §5, 02-actors-permissions, US-1001 AC3. `Makefile`: 08 §2.4, §3. `modules/identity/tests/factories.py`, `backend/conftest.py`: 02 §9.5, 12 §4. Test: 02 §9.2 (tên file test), §9.5 |
| Model | `Account(AbstractBaseUser, BaseModel)` trong `modules/identity/models/account.py`; import `AbstractBaseUser`, `BaseUserManager` từ `django.contrib.auth.base_user` vì `django.contrib.auth` không có trong `INSTALLED_APPS`. Cột và ràng buộc đúng 03 §2.1; `USERNAME_FIELD = EMAIL_FIELD = "email"`, `REQUIRED_FIELDS = []`. `kind`, `language` là `TextChoices` trong `modules/identity/constants.py` (`AccountKind`, `Language`), mỗi cột kèm `CheckConstraint` theo 03 §0.2. Ràng buộc: `UniqueConstraint(Lower("email"))`, `CHECK(anonymized_at IS NULL OR is_active = false)` |
| Manager | `AccountManager(BaseUserManager.from_queryset(BaseQuerySet))`, gán `objects = AccountManager()` trên `Account`, để có hàm của user manager mà vẫn giữ việc tự gán `updated_at` của `BaseModel` (03 §0.1). Email chuẩn hoá bằng `strip().lower()` trước khi ghi, vì 03 §2.1 lưu chữ thường |
| Migration | `modules/migrations/0001_initial.py` chỉ chứa `Account`, phụ thuộc `("shared", "0004_idempotency_key")`. Không có bảng `auth_*` vì không cài `django.contrib.auth` (03 §0.9); AC4 kiểm bằng danh sách bảng sau migrate |
| Service | `modules/identity/services/accounts.py::create_staff_account(*, email, password, kind, full_name="") -> Account` chuẩn hoá email, rồi kiểm trong service (sửa khi review, P1/B1, T2/B4): email khác rỗng, đúng định dạng (`EmailValidator`), tối đa 254 ký tự → sai thì `InvalidEmail` (`code = "INVALID_EMAIL"`, 422); mật khẩu qua `validate_password(password, user=<Account chưa lưu>)` → không đạt thì `WeakPassword` (`code = "WEAK_PASSWORD"`, 422, `details` mang danh sách thông báo của validator). Cả hai là `DomainError` trong `modules/identity/exceptions.py`. Ghi trong `transaction.atomic`; không kiểm trùng trước bằng truy vấn, chỉ đổi `IntegrityError` của ràng buộc `identity_account_email_lower_uniq` thành `EmailAlreadyUsed` (`code = "EMAIL_ALREADY_USED"`, 409), vi phạm khác ném lại (sửa khi review, B2/B5). `kind` chỉ nhận `staff`/`admin`, khác thì `ValueError` (lỗi của bên gọi). Back-office tạo Staff (US-1001 AC1) dùng lại service này. Chưa thêm mã lỗi vào 04 §3 vì chưa có endpoint |
| Lệnh | `create_staff [--admin] [--email X] [--full-name Y]` ở `modules/management/commands/` (02 §5). Thiếu `--email` thì hỏi; mật khẩu luôn nhập qua `getpass` hai lần, không có cờ `--password` để mật khẩu không vào lịch sử shell. Lệnh chỉ đọc input, kiểm hai lần nhập khớp, gọi service và đổi `DomainError` thành `CommandError` (độ mạnh mật khẩu do service kiểm, sửa khi review T2/B4). Tạo xong ghi log structlog `staff_account_created` với `account_id` (chuỗi UUID), `kind`, không ghi email (PII); test log đọc qua fixture `json_logging` (12 §4). Test giả `input`/`getpass` ở seam của lệnh |
| Độ mạnh mật khẩu | Thêm `AUTH_PASSWORD_VALIDATORS` vào `base.py` theo 05 §3: `MinimumLengthValidator` (8), `UserAttributeSimilarityValidator`, `CommonPasswordValidator`, `NumericPasswordValidator`. Không đổi `PASSWORD_HASHERS` (Argon2 ở M1) |
| `make create-admin` | `uv run python manage.py create_staff --admin`, chạy tương tác; thêm vào `.PHONY` |
| Fixture | **Khác *Việc cần làm*:** `staff_client`, `admin_client` ở `backend/conftest.py` tạo Account bằng factory rồi gọi `APIClient.force_authenticate(user=account, token={"aud": "backoffice"})`, thay vì để trống xác thực. Lý do: `IsStaff`/`IsAdmin` (`shared/api/permissions.py`) đòi `request.auth["aud"] == "backoffice"`, nên fixture để trống không qua được permission nào. M1 thay bằng JWT thật, giữ nguyên tên fixture. Có test chứng minh mỗi fixture qua đúng permission. `customer_client` để tới M6 |
| Test migration của `shared` | Thêm khi code S1, người dùng duyệt: `shared/tests/test_migrations.py::test_reverse_drops_function_but_keeps_extensions` chạy `migrate shared zero`, kéo theo gỡ `modules.0001`; khối `finally` đổi sang `call_command("migrate")` để tạo lại mọi app, không chỉ `shared` |
| Factory | `AccountFactory(DjangoModelFactory[Account])` ở `modules/identity/tests/factories.py`, email theo `factory.Sequence`, `kind = staff`, mật khẩu qua `factory.django.Password` (sửa khi review, B8); trait `admin` |

## Kế hoạch

Sinh bằng `plan.py` từ state của skill. Mỗi task là đúng một commit có trailer `Task: <task>`.

| Task | AC | Seam | Test dự kiến | File | Sau |
| --- | --- | --- | --- | --- | --- |
| S1 | 1, 2, 4 | migrate trên DB test rồi đọc schema (connection.introspection) và ghi Account qua ORM | `modules/identity/tests/test_models_account.py::test_initial_migration_creates_identity_account`<br>`modules/identity/tests/test_models_account.py::test_email_unique_ignores_case`<br>`modules/identity/tests/test_models_account.py::test_anonymized_account_must_be_inactive`<br>`modules/identity/tests/test_models_account.py::test_unknown_kind_rejected_by_db`<br>`modules/identity/tests/test_models_account.py::test_no_django_auth_tables_after_migrate`<br>`modules/identity/tests/test_models_account.py::test_django_admin_not_installed_in_any_settings` | `backend/modules/identity/constants.py`<br>`backend/modules/identity/models/__init__.py`<br>`backend/modules/identity/models/account.py`<br>`backend/modules/models.py`<br>`backend/modules/migrations/__init__.py`<br>`backend/modules/migrations/0001_initial.py`<br>`backend/config/settings/base.py`<br>`backend/modules/identity/tests/__init__.py`<br>`backend/modules/identity/tests/factories.py`<br>`backend/modules/identity/tests/test_models_account.py` | — |
| S2 | 3 | service create_staff_account gọi trực tiếp; lệnh qua call_command với input/getpass giả | `modules/identity/tests/test_services_accounts.py::test_create_staff_account_stores_lowercase_email`<br>`modules/identity/tests/test_services_accounts.py::test_create_staff_account_rejects_email_used_ignoring_case`<br>`modules/identity/tests/test_services_accounts.py::test_create_staff_account_rejects_customer_kind`<br>`modules/identity/tests/test_commands_create_staff.py::test_create_staff_admin_creates_admin_account`<br>`modules/identity/tests/test_commands_create_staff.py::test_create_staff_same_email_raises_command_error`<br>`modules/identity/tests/test_commands_create_staff.py::test_create_staff_rejects_weak_password`<br>`modules/identity/tests/test_commands_create_staff.py::test_create_staff_rejects_mismatched_password` | `backend/modules/identity/exceptions.py`<br>`backend/modules/identity/services/__init__.py`<br>`backend/modules/identity/services/accounts.py`<br>`backend/modules/management/__init__.py`<br>`backend/modules/management/commands/__init__.py`<br>`backend/modules/management/commands/create_staff.py`<br>`backend/config/settings/base.py`<br>`backend/Makefile`<br>`backend/modules/identity/tests/test_services_accounts.py`<br>`backend/modules/identity/tests/test_commands_create_staff.py` | S1 |
| S3 | — | view DRF tạm trong test với IsStaff/IsAdmin, gọi qua fixture client | `modules/identity/tests/test_conftest_clients.py::test_staff_client_passes_is_staff`<br>`modules/identity/tests/test_conftest_clients.py::test_admin_client_passes_is_admin` | `backend/conftest.py`<br>`backend/modules/identity/tests/test_conftest_clients.py` | S1 |

Commit dự kiến: `plan` → `S1` → `S2` → `S3` → `R1 (khi review cần sửa)` → `sync` → `close`.

## Acceptance criteria

- [x] `make migrate` trên DB trống tạo `identity_account` trong migration `0001` của `modules`.
- [x] Hai email chỉ khác hoa thường không tạo được hai Tài khoản (ràng buộc DB `UNIQUE(lower(email))`).
- [x] `create_staff --admin` tạo Tài khoản `kind = admin`; chạy lại cùng email báo lỗi rõ ràng.
- [x] Không có bảng group/permission của Django sau migrate. `django.contrib.admin` không có trong `INSTALLED_APPS` ở mọi môi trường (không dùng Django Admin, [08 mục 2.4](../../../docs/architecture/08-local-development.md#24-chạy)).

## Comments

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
