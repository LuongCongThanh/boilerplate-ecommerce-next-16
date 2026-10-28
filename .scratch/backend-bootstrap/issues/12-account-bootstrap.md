# Model `Account` trong migration đầu tiên và lệnh `create_staff`

Status: ready-for-agent

Blocked by: 09

Spec: [spec.md](../spec.md)

## Việc cần làm

- `modules/identity/models/account.py`: `Account` kế thừa `AbstractBaseUser` và `BaseModel`, không kế thừa `PermissionsMixin`, đủ cột và ràng buộc ở [03 mục 2.1](../../../docs/architecture/03-data-model.md#21-identity_account-tài-khoản). `AUTH_USER_MODEL = "modules.Account"`; đây là migration đầu tiên của `modules/migrations/`.
- `modules/models.py` import model của identity; `Meta.db_table = "identity_account"`.
- Lệnh `manage.py create_staff [--admin]` tạo Tài khoản `staff` hoặc `admin`; email trùng (không phân biệt hoa thường) với bất kỳ Tài khoản nào thì từ chối (US-1001 AC2, AC3).
- `modules/identity/tests/factories.py` cho Account; fixture `staff_client`, `admin_client` ở `backend/conftest.py` để trống phần xác thực, sẽ hoàn thiện khi có JWT ở M1.
- Hash mật khẩu tạm dùng mặc định của Django; Argon2 thêm ở M1 cùng luồng đăng nhập.

## Acceptance criteria

- [ ] `make migrate` trên DB trống tạo `identity_account` trong migration `0001` của `modules`.
- [ ] Hai email chỉ khác hoa thường không tạo được hai Tài khoản (ràng buộc DB `UNIQUE(lower(email))`).
- [ ] `create_staff --admin` tạo Tài khoản `kind = admin`; chạy lại cùng email báo lỗi rõ ràng.
- [ ] Không có bảng group/permission của Django sau migrate.
