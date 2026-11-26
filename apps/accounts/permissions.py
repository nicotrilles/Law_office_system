"""Central authorization: may this user do this?

This is the ONLY place that decides. It reads the user's role, then the permissions that role holds
(tables role_permissions and permissions). It never looks at a role NAME, has no superuser shortcut,
and never uses Django's own Group or Permission system.

The answer to "is it allowed?" has three possible outcomes, and they must never be confused:
- True  : the lookup worked and the user holds the permission.
- False : the lookup worked and the user does NOT hold it (an ordinary denial, HTTP 403).
- raises PermissionLookupError : the lookup itself FAILED (database or infrastructure problem).
  This is not a denial. The decorator turns it into HTTP 503.
"""
import logging

from django.core.exceptions import ImproperlyConfigured
from django.db import Error as DatabaseError

from . import reference_data
from .models import RolePermission

logger = logging.getLogger(__name__)

_CACHE_ATTRIBUTE = "_permission_keys_cache"


class PermissionLookupError(Exception):
    """The permissions could not be looked up. Access is denied, but this is NOT a normal denial."""


def known_permission_keys():
    # Plain Python data: no database. Read at call time so the registry is always the current one.
    return {definition.key for definition in reference_data.PERMISSION_DEFINITIONS}


def require_known_key(key):
    if key not in known_permission_keys():
        raise ImproperlyConfigured(
            f"Permission key {key!r} is not in reference_data.PERMISSION_DEFINITIONS. "
            "Check the spelling, or add the (approved) definition first."
        )


def _load_keys(role_id):
    """The one database query: every permission key held by a role."""
    return frozenset(
        RolePermission.objects.filter(role_id=role_id).values_list("permission__permission_key", flat=True)
    )


def get_permission_keys(user):
    """Return the set of permission keys the user holds.

    Anonymous users, inactive users, and users without a role hold nothing (no query is made).
    The answer is remembered on the user object, which lives for one request, so a page that checks
    several permissions asks the database once. A new request always starts fresh, so a grant or
    revoke takes effect on the very next request.
    """
    if not (user.is_authenticated and user.is_active):
        return frozenset()
    role_id = getattr(user, "role_id", None)
    if role_id is None:
        return frozenset()

    cached = getattr(user, _CACHE_ATTRIBUTE, None)
    if isinstance(cached, PermissionLookupError):
        raise cached  # the lookup already failed during this request: do not retry
    if cached is not None:
        return cached

    try:
        keys = _load_keys(role_id)
    except DatabaseError as exc:
        logger.exception("Permission lookup failed for user_id=%s. Access is denied (HTTP 503).", user.pk)
        failure = PermissionLookupError("The permission lookup failed.")
        failure.__cause__ = exc
        setattr(user, _CACHE_ATTRIBUTE, failure)
        raise failure
    setattr(user, _CACHE_ATTRIBUTE, keys)
    return keys


def has_permission(user, key):
    """True or False. Raises ImproperlyConfigured for an unknown key and PermissionLookupError on failure."""
    require_known_key(key)
    return key in get_permission_keys(user)
