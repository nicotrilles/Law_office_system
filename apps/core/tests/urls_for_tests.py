"""URL config used only by tests: one route that deliberately crashes."""
from django.urls import include, path

from apps.core import views as core_views

handler400 = "apps.core.views.bad_request"
handler403 = "apps.core.views.permission_denied"
handler404 = "apps.core.views.page_not_found"
handler500 = "apps.core.views.server_error"


def boom(request):
    raise RuntimeError("SECRET-INTERNAL-DETAIL")


urlpatterns = [
    path("boom/", boom),
    path("", include("apps.core.urls")),
]
