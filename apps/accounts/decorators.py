"""View guard: @permission_required("client.view").

- Anonymous visitor            -> redirect to the sign-in page (and back afterwards)
- Signed in, lacks permission  -> HTTP 403 (the permission check WORKED and said no)
- Permission lookup failed     -> HTTP 503 (the check could not be made; access is still denied)
- Holds the permission         -> the view runs
"""
import logging
from functools import wraps

from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.template.loader import render_to_string

from .permissions import PermissionLookupError, has_permission, require_known_key

logger = logging.getLogger(__name__)


def _service_unavailable():
    # Rendered without a request context: this page must not need the database.
    return HttpResponse(render_to_string("errors/503.html"), status=503)


def permission_required(key):
    # Runs when Python reads the decorator line (import time). It uses only the in-code registry,
    # never the database, so a misspelt key fails at startup instead of denying everybody quietly.
    require_known_key(key)

    def decorator(view):
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            user = request.user
            if not user.is_authenticated:
                return redirect_to_login(request.get_full_path())
            try:
                allowed = has_permission(user, key)
            except PermissionLookupError:
                return _service_unavailable()  # already logged with the technical details
            if not allowed:
                logger.warning("Permission denied: user_id=%s permission=%s method=%s path=%s",
                               user.pk, key, request.method, request.path)
                raise PermissionDenied
            return view(request, *args, **kwargs)

        return wrapper

    return decorator
