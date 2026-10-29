"""Chuẩn hoá số điện thoại Việt Nam về E.164 (03 mục 0.6)."""

import phonenumbers


class InvalidPhoneNumber(ValueError):
    """Không phải số hợp lệ thuộc Việt Nam. Serializer đổi thành lỗi validate của field."""


def normalize_vn_phone(raw: str) -> str:
    """Trả số E.164, ví dụ `0901234567` và `+84 901 234 567` đều thành `+84901234567`.

    Nhận mọi số hợp lệ thuộc Việt Nam, kể cả số cố định; số hợp lệ của nước khác bị từ chối.
    Không tự đoán số thiếu đầu số.

    Raises:
        InvalidPhoneNumber: đầu vào không phải số hợp lệ thuộc Việt Nam. Thông báo lỗi không
            chứa số gốc để không lọt vào log.
    """
    try:
        number = phonenumbers.parse(raw, "VN")
    except phonenumbers.NumberParseException as exc:
        raise InvalidPhoneNumber("Số điện thoại không hợp lệ") from exc
    if not phonenumbers.is_valid_number_for_region(number, "VN"):
        raise InvalidPhoneNumber("Số điện thoại không hợp lệ")
    return phonenumbers.format_number(number, phonenumbers.PhoneNumberFormat.E164)
