"""
Production settings.

Hosting and HTTPS are still undecided (X-UQ-008), so the HTTPS-related options below are
controlled by environment variables. They default to the SECURE value. If the office
serves the system over plain HTTP on a local network, these must be set to False
explicitly (and that decision should be documented).
"""
from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F401,F403
from .base import ALLOWED_HOSTS, env

DEBUG = False

if not ALLOWED_HOSTS:
    raise ImproperlyConfigured("ALLOWED_HOSTS must be set for production.")

SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)
SESSION_COOKIE_SECURE = env.bool("SESSION_COOKIE_SECURE", default=True)
CSRF_COOKIE_SECURE = env.bool("CSRF_COOKIE_SECURE", default=True)
# HSTS is "sticky" in browsers, so it stays off (0) until HTTPS is confirmed to work.
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=0)
