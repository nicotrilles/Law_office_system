"""
Shared views: home page, health check, and centralised error pages.

Error pages show a generic message only. Technical details go to the server log,
never to the browser (NFR-SEC and the "no sensitive server errors" rule).
"""
import logging

from django.contrib.auth.decorators import login_required
from django.db import Error as DatabaseError
from django.db import connection
from django.http import HttpResponseServerError, JsonResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.views.decorators.http import require_GET

logger = logging.getLogger(__name__)


@login_required
def home(request):
    return render(request, "home.html")


@require_GET
def health(request):
    """Reports only whether the app can reach its database. No versions, hosts, or errors."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except DatabaseError:
        logger.exception("Health check failed: database is unreachable")
        return JsonResponse({"status": "unavailable"}, status=503)
    return JsonResponse({"status": "ok"})


def bad_request(request, exception=None):
    return render(request, "errors/400.html", status=400)


def permission_denied(request, exception=None):
    return render(request, "errors/403.html", status=403)


def page_not_found(request, exception=None):
    return render(request, "errors/404.html", status=404)


def server_error(request):
    # Rendered without a request context so this page still works if middleware or the
    # database is the thing that failed.
    return HttpResponseServerError(render_to_string("errors/500.html"))


def csrf_failure(request, reason=""):
    logger.warning("CSRF check failed for %s %s", request.method, request.path)
    return render(request, "errors/403.html", status=403)
