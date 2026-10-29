"""`handler404` và `handler500` của Django trả `ErrorDTO` như lỗi trong view DRF (04 mục 3)."""

from django.http import HttpRequest, JsonResponse
from django.utils.translation import gettext_lazy as _

from shared.api.exception_handler import error_body


def not_found(request: HttpRequest, exception: Exception) -> JsonResponse:
    return JsonResponse(error_body("NOT_FOUND", _("Không tìm thấy.")), status=404)


def server_error(request: HttpRequest) -> JsonResponse:
    # Không đưa nội dung exception vào response; Django đã log kèm traceback
    return JsonResponse(error_body("INTERNAL_ERROR", _("Lỗi hệ thống.")), status=500)
