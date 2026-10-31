# Model `Account` trong migration đầu tiên và lệnh `create_staff`

Status: resolved

**PR:** #42

Blocked by: 09

Spec: [spec.md](../../spec.md)

## Việc cần làm

- `modules/identity/models/account.py`: `Account` kế thừa `AbstractBaseUser` và `BaseModel`, không kế thừa `PermissionsMixin`, đủ cột và ràng buộc ở [03 mục 2.1](../../../../docs/architecture/03-data-model.md#21-identity_account-tài-khoản). `AUTH_USER_MODEL = "modules.Account"`; đây là migration đầu tiên của `modules/migrations/`.
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

## Acceptance criteria

- [x] `make migrate` trên DB trống tạo `identity_account` trong migration `0001` của `modules`.
- [x] Hai email chỉ khác hoa thường không tạo được hai Tài khoản (ràng buộc DB `UNIQUE(lower(email))`).
- [x] `create_staff --admin` tạo Tài khoản `kind = admin`; chạy lại cùng email báo lỗi rõ ràng.
- [x] Không có bảng group/permission của Django sau migrate. `django.contrib.admin` không có trong `INSTALLED_APPS` ở mọi môi trường (không dùng Django Admin, [08 mục 2.4](../../../../docs/architecture/08-local-development.md#24-chạy)).
