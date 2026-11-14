"""Root URL configuration. Each module adds its own urls.py under apps/."""
from django.urls import include, path

# Centralised error pages (see apps/core/views.py). They never reveal server details.
handler400 = "apps.core.views.bad_request"
handler403 = "apps.core.views.permission_denied"
handler404 = "apps.core.views.page_not_found"
handler500 = "apps.core.views.server_error"

urlpatterns = [
    path("", include("apps.core.urls")),
]
