from django.conf import settings
from django.urls import URLPattern, URLResolver, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.permissions import AllowAny

from shared.health import views as health

# Route lạ và exception không bắt cũng trả ErrorDTO (04 mục 3)
handler404 = "shared.api.views.not_found"
handler500 = "shared.api.views.server_error"

urlpatterns: list[URLPattern | URLResolver] = [
    path("healthz", health.healthz, name="healthz"),
    path("readyz", health.readyz, name="readyz"),
]

if settings.API_DOCS_ENABLED:
    urlpatterns += [
        # Mặc định mọi view cần đăng nhập; schema và Swagger UI để công khai
        path(
            "api/schema/",
            SpectacularAPIView.as_view(permission_classes=[AllowAny]),
            name="schema",
        ),
        path(
            "api/docs/",
            SpectacularSwaggerView.as_view(url_name="schema", permission_classes=[AllowAny]),
            name="docs",
        ),
    ]
