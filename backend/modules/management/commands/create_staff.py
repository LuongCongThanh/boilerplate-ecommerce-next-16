"""Tạo Tài khoản Staff hoặc Admin cho back-office (02 mục 5, 08 mục 2.4 bước 5).

Thiếu `--email` thì hỏi. Mật khẩu luôn nhập qua `getpass` hai lần, không có cờ `--password` để
mật khẩu không nằm trong lịch sử shell; độ mạnh kiểm bằng `AUTH_PASSWORD_VALIDATORS` (05 mục 3).
"""

from getpass import getpass

import structlog
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError, CommandParser

from modules.identity.constants import AccountKind
from modules.identity.exceptions import EmailAlreadyUsed
from modules.identity.models import Account
from modules.identity.services.accounts import create_staff_account

logger = structlog.get_logger(__name__)


class Command(BaseCommand):
    help = "Tạo Tài khoản Staff (Admin khi có --admin); mật khẩu nhập từ bàn phím."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--admin", action="store_true", help="Tạo Tài khoản Admin.")
        parser.add_argument("--email", help="Email đăng nhập; bỏ trống thì lệnh hỏi.")
        parser.add_argument("--full-name", default="", help="Họ tên hiển thị.")

    def handle(self, *args: object, **options: object) -> None:
        kind = AccountKind.ADMIN if options["admin"] else AccountKind.STAFF
        email = str(options["email"] or input("Email: "))
        full_name = str(options["full_name"])
        password = getpass("Mật khẩu: ")
        if getpass("Nhập lại mật khẩu: ") != password:
            raise CommandError("Hai lần nhập mật khẩu không khớp")
        # Account chưa lưu, chỉ để validator so mật khẩu với email, họ tên
        candidate = Account(
            email=Account.objects.normalize_email(email), kind=kind, full_name=full_name
        )
        try:
            validate_password(password, user=candidate)
        except ValidationError as exc:
            raise CommandError("Mật khẩu chưa đủ mạnh: " + " ".join(exc.messages)) from exc
        try:
            account = create_staff_account(
                email=email, password=password, kind=kind, full_name=full_name
            )
        except EmailAlreadyUsed as exc:
            raise CommandError(str(exc.message)) from exc
        # Không ghi email vào log (PII, 02 mục 9.6)
        logger.info("staff_account_created", account_id=account.id, kind=account.kind)
