# Model `Account` trong migration đầu tiên và lệnh `create_staff`

Status: ready-for-agent

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
| Service | `modules/identity/services/accounts.py::create_staff_account(*, email, password, kind, full_name="") -> Account` mở `transaction.atomic`, chuẩn hoá email, kiểm trùng không phân biệt hoa thường, bắt `IntegrityError` của `UniqueConstraint` khi hai lệnh chạy cùng lúc; trùng thì ném `EmailAlreadyUsed` (`modules/identity/exceptions.py`, `DomainError`, `code = "EMAIL_ALREADY_USED"`, `http_status = 409`). `kind` chỉ nhận `staff`/`admin`. Back-office tạo Staff (US-1001 AC1) dùng lại service này. Chưa thêm mã lỗi vào 04 §3 vì chưa có endpoint |
| Lệnh | `create_staff [--admin] [--email X] [--full-name Y]` ở `modules/management/commands/` (02 §5). Thiếu `--email` thì hỏi; mật khẩu luôn nhập qua `getpass` hai lần, không có cờ `--password` để mật khẩu không vào lịch sử shell. Kiểm bằng `validate_password` (05 §3). Lỗi đổi thành `CommandError`; tạo xong ghi log structlog `staff_account_created` với `account_id`, `kind`, không ghi email (PII). Test giả `input`/`getpass` ở seam của lệnh |
| Độ mạnh mật khẩu | Thêm `AUTH_PASSWORD_VALIDATORS` vào `base.py` theo 05 §3: `MinimumLengthValidator` (8), `UserAttributeSimilarityValidator`, `CommonPasswordValidator`, `NumericPasswordValidator`. Không đổi `PASSWORD_HASHERS` (Argon2 ở M1) |
| `make create-admin` | `uv run python manage.py create_staff --admin`, chạy tương tác; thêm vào `.PHONY` |
| Fixture | **Khác *Việc cần làm*:** `staff_client`, `admin_client` ở `backend/conftest.py` tạo Account bằng factory rồi gọi `APIClient.force_authenticate(user=account, token={"aud": "backoffice"})`, thay vì để trống xác thực. Lý do: `IsStaff`/`IsAdmin` (`shared/api/permissions.py`) đòi `request.auth["aud"] == "backoffice"`, nên fixture để trống không qua được permission nào. M1 thay bằng JWT thật, giữ nguyên tên fixture. Có test chứng minh mỗi fixture qua đúng permission. `customer_client` để tới M6 |
| Factory | `AccountFactory(DjangoModelFactory[Account])` ở `modules/identity/tests/factories.py`, email theo `factory.Sequence`, `kind = staff`, mật khẩu đặt qua `set_password`; trait `admin` |

## Kế hoạch

Sinh bằng `plan.py` từ state của skill. Mỗi task là đúng một commit có trailer `Task: <task>`.

| Task | AC | Seam | Test dự kiến | File | Sau |
| --- | --- | --- | --- | --- | --- |
| S1 | 1, 2, 4 | migrate trên DB test rồi đọc schema (connection.introspection) và ghi Account qua ORM | `modules/identity/tests/test_models_account.py::test_initial_migration_creates_identity_account`<br>`modules/identity/tests/test_models_account.py::test_email_unique_ignores_case`<br>`modules/identity/tests/test_models_account.py::test_anonymized_account_must_be_inactive`<br>`modules/identity/tests/test_models_account.py::test_unknown_kind_rejected_by_db`<br>`modules/identity/tests/test_models_account.py::test_no_django_auth_tables_after_migrate`<br>`modules/identity/tests/test_models_account.py::test_django_admin_not_installed_in_any_settings` | `backend/modules/identity/constants.py`<br>`backend/modules/identity/models/__init__.py`<br>`backend/modules/identity/models/account.py`<br>`backend/modules/models.py`<br>`backend/modules/migrations/__init__.py`<br>`backend/modules/migrations/0001_initial.py`<br>`backend/config/settings/base.py`<br>`backend/modules/identity/tests/__init__.py`<br>`backend/modules/identity/tests/factories.py`<br>`backend/modules/identity/tests/test_models_account.py` | — |
| S2 | 3 | service create_staff_account gọi trực tiếp; lệnh qua call_command với input/getpass giả | `modules/identity/tests/test_services_accounts.py::test_create_staff_account_stores_lowercase_email`<br>`modules/identity/tests/test_services_accounts.py::test_create_staff_account_rejects_email_used_ignoring_case`<br>`modules/identity/tests/test_services_accounts.py::test_create_staff_account_rejects_customer_kind`<br>`modules/identity/tests/test_commands_create_staff.py::test_create_staff_admin_creates_admin_account`<br>`modules/identity/tests/test_commands_create_staff.py::test_create_staff_same_email_raises_command_error`<br>`modules/identity/tests/test_commands_create_staff.py::test_create_staff_rejects_weak_password`<br>`modules/identity/tests/test_commands_create_staff.py::test_create_staff_rejects_mismatched_password` | `backend/modules/identity/exceptions.py`<br>`backend/modules/identity/services/__init__.py`<br>`backend/modules/identity/services/accounts.py`<br>`backend/modules/management/__init__.py`<br>`backend/modules/management/commands/__init__.py`<br>`backend/modules/management/commands/create_staff.py`<br>`backend/config/settings/base.py`<br>`backend/Makefile`<br>`backend/modules/identity/tests/test_services_accounts.py`<br>`backend/modules/identity/tests/test_commands_create_staff.py` | S1 |
| S3 | — | view DRF tạm trong test với IsStaff/IsAdmin, gọi qua fixture client | `modules/identity/tests/test_conftest_clients.py::test_staff_client_passes_is_staff`<br>`modules/identity/tests/test_conftest_clients.py::test_admin_client_passes_is_admin` | `backend/conftest.py`<br>`backend/modules/identity/tests/test_conftest_clients.py` | S1 |

Commit dự kiến: `plan` → `S1` → `S2` → `S3` → `R1 (khi review cần sửa)` → `sync` → `close`.

## Acceptance criteria

- [ ] `make migrate` trên DB trống tạo `identity_account` trong migration `0001` của `modules`.
- [ ] Hai email chỉ khác hoa thường không tạo được hai Tài khoản (ràng buộc DB `UNIQUE(lower(email))`).
- [ ] `create_staff --admin` tạo Tài khoản `kind = admin`; chạy lại cùng email báo lỗi rõ ràng.
- [ ] Không có bảng group/permission của Django sau migrate. `django.contrib.admin` không có trong `INSTALLED_APPS` ở mọi môi trường (không dùng Django Admin, [08 mục 2.4](../../../docs/architecture/08-local-development.md#24-chạy)).
