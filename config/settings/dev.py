"""Development settings. Never use these on a real server."""
from .base import *  # noqa: F401,F403
from .base import ALLOWED_HOSTS, env  # noqa: F401

DEBUG = True

if not ALLOWED_HOSTS:
    ALLOWED_HOSTS = ["localhost", "127.0.0.1"]
