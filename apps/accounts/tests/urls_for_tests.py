"""Test-only URL configuration: two protected pages guarded with approved permission keys.

It includes the real accounts and core URLs because the 403 page's base template links to the
'home' and 'accounts:logout' routes. (Not collected as a test: the file name does not start with test.)
"""
from django.http import HttpResponse
from django.urls import include, path

from apps.accounts.decorators import permission_required

handler400 = "apps.core.views.bad_request"
handler403 = "apps.core.views.permission_denied"
handler404 = "apps.core.views.page_not_found"
handler500 = "apps.core.views.server_error"

calls = []  # lets a test prove that a refused view body never ran


@permission_required("client.view")
def clients_page(request):
    calls.append(("view", request.method))
    return HttpResponse("clients page")


@permission_required("client.create")
def create_page(request):
    calls.append(("create", request.method))
    return HttpResponse("created" if request.method == "POST" else "create form")


urlpatterns = [
    path("test/clients/", clients_page),
    path("test/clients/new/", create_page),
    path("accounts/", include("apps.accounts.urls")),
    path("", include("apps.core.urls")),
]
