"""Failed-login throttling (provisional defaults: LOGIN_MAX_ATTEMPTS and LOGIN_LOCKOUT_MINUTES).

How it works
- Failed sign-ins are counted per (username, network address). The username is compared without
  regard to letter case and the pair is stored only as a SHA-256 hash, never in readable form.
- Counting happens in a FIXED window that starts at the first failure and lasts LOGIN_LOCKOUT_MINUTES.
  Reaching LOGIN_MAX_ATTEMPTS locks that pair for LOGIN_LOCKOUT_MINUTES.
- While locked, attempts are refused BEFORE the password is checked, and they do NOT extend the lock.
- A successful sign-in clears the count.
- A username that does not exist is counted exactly like one that does, so the lock reveals nothing.
- Counters live in the PostgreSQL-backed cache "login_throttle" (table login_throttle_cache, created
  by `python manage.py createcachetable`). If that store is unavailable, sign-in FAILS CLOSED.

The cache's own expiry is only housekeeping. Whether a pair is locked is decided from the timestamps
stored in the value, using now() below, which tests replace to move time.
Known limit: read-then-write is not atomic, so a burst of simultaneous attempts can slip a few extra
guesses through before the lock lands.
"""
import hashlib
import logging
import time

from django.conf import settings
from django.core.cache import caches
from django.db import Error as DatabaseError

logger = logging.getLogger(__name__)

CACHE_ALIAS = "login_throttle"


class ThrottleUnavailable(Exception):
    """The throttle store could not be read or written."""


def now():
    return time.time()


def client_address(request):
    # REMOTE_ADDR only. Forwarded-address headers are NOT trusted: a client could invent them.
    return (request.META.get("REMOTE_ADDR") if request is not None else None) or "unknown"


def _digest(username, address):
    identity = f"{username.strip().casefold()}|{address}"
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()


def _window_seconds():
    return settings.LOGIN_LOCKOUT_MINUTES * 60


def _guard(operation):
    try:
        return operation()
    except DatabaseError:
        logger.exception(
            "Sign-in throttle store unavailable. Sign-in is refused until it is fixed. "
            "Run: python manage.py createcachetable"
        )
        raise ThrottleUnavailable from None


def _get(digest):
    return _guard(lambda: caches[CACHE_ALIAS].get("login:" + digest))


def is_locked(username, address):
    state = _get(_digest(username, address))
    return bool(state) and state["locked_until"] > now()


def record_failure(username, address):
    digest = _digest(username, address)
    state = _get(digest)
    t = now()
    if state and state["locked_until"] > t:
        return  # already locked: later attempts neither count nor extend the lock
    window = _window_seconds()
    if not state or t - state["window_started_at"] >= window:
        state = {"failures": 0, "window_started_at": t, "locked_until": 0}
    state["failures"] += 1
    if state["failures"] >= settings.LOGIN_MAX_ATTEMPTS:
        state["locked_until"] = t + window
        logger.warning("Sign-in lockout started (key %s)", digest[:12])
    _guard(lambda: caches[CACHE_ALIAS].set("login:" + digest, state, timeout=2 * window))


def clear(username, address):
    digest = _digest(username, address)
    _guard(lambda: caches[CACHE_ALIAS].delete("login:" + digest))
