"""
Base settings shared by every environment.

Secrets and machine-specific values come from environment variables (optionally
loaded from a git-ignored ".env" file). Nothing secret is stored in this file.
"""
import logging.handlers  # noqa: F401  (makes sure the rotating file handler is importable)
import os
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()

# Load ".env" if present. Real environment variables take priority over the file.
# DJANGO_ENV_FILE lets tests (or deployments) point at a different file.
_env_file = Path(os.environ.get("DJANGO_ENV_FILE", BASE_DIR / ".env"))
if _env_file.exists():
    environ.Env.read_env(_env_file)

# ---------------------------------------------------------------------------
# Core
# ---------------------------------------------------------------------------
SECRET_KEY = env("SECRET_KEY")  # No default on purpose: the app must not start without one.
DEBUG = env.bool("DEBUG", default=False)  # Safe default. dev.py turns it on explicitly.
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",  # Provides login/session/password machinery. Its own Permission/Group
    # tables exist but are NOT used: ROLES / PERMISSIONS / ROLE_PERMISSIONS are the authority.
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Project apps
    "apps.core",
    "apps.accounts",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# ---------------------------------------------------------------------------
# Database (PostgreSQL)
# ---------------------------------------------------------------------------
DATABASES = {"default": env.db("DATABASE_URL")}
DATABASES["default"]["CONN_MAX_AGE"] = env.int("DB_CONN_MAX_AGE", default=60)
# Transactions are opened explicitly (transaction.atomic) around the operations that must
# succeed or fail together, instead of wrapping every request.
DATABASES["default"]["ATOMIC_REQUESTS"] = False

# Schema primary keys are BIGINT identity columns.
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# Custom user model: maps to the USERS table of the logical schema.
# This MUST be set before the first migration is ever run.
# ---------------------------------------------------------------------------
AUTH_USER_MODEL = "accounts.User"

# Where people are sent to sign in, after signing in, and after signing out.
LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "home"
LOGOUT_REDIRECT_URL = "accounts:login"

# Caches. Django requires "default" (nothing uses it). "login_throttle" holds failed-sign-in counters in
# PostgreSQL, so they survive restarts and are shared by every server process. Create its table once with:
#     python manage.py createcachetable
# (Test databases get the table automatically.)
CACHES = {
    "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
    "login_throttle": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "login_throttle_cache",
    },
}

# ---------------------------------------------------------------------------
# Provisional security defaults (D5). These are technical development settings,
# NOT confirmed office policy. They are configurable through environment variables.
# ---------------------------------------------------------------------------
PASSWORD_MIN_LENGTH = env.int("PASSWORD_MIN_LENGTH", default=12)
SESSION_IDLE_TIMEOUT_SECONDS = env.int("SESSION_IDLE_TIMEOUT_SECONDS", default=1800)
LOGIN_MAX_ATTEMPTS = env.int("LOGIN_MAX_ATTEMPTS", default=5)  # Used from Milestone 2
LOGIN_LOCKOUT_MINUTES = env.int("LOGIN_LOCKOUT_MINUTES", default=15)  # Used from Milestone 2

PASSWORD_HASHERS = ["django.contrib.auth.hashers.Argon2PasswordHasher"]

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
        "OPTIONS": {"user_attributes": ("username", "full_name")},
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": PASSWORD_MIN_LENGTH},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Sessions: idle timeout (the clock restarts on every request) and no persistence after the
# browser closes. Cookies are not readable by JavaScript.
SESSION_COOKIE_AGE = SESSION_IDLE_TIMEOUT_SECONDS
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_FAILURE_VIEW = "apps.core.views.csrf_failure"

SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"

# ---------------------------------------------------------------------------
# Internationalisation. Timestamps are stored in UTC and shown in TIME_ZONE.
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = env("TIME_ZONE", default="UTC")
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Static files (CSS/JS shipped with the app) and document storage
# ---------------------------------------------------------------------------
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

# Uploaded and generated legal documents live here. This folder is deliberately NOT
# exposed through any URL; files will only be served by permission-checked views.
# Hosting and backup are still open decisions (X-UQ-008, X-UQ-009).
DOCUMENT_STORAGE_ROOT = Path(env("DOCUMENT_STORAGE_ROOT", default=str(BASE_DIR / "storage")))

# ---------------------------------------------------------------------------
# Logging: console plus a rotating file. Passwords and secrets are never logged.
# ---------------------------------------------------------------------------
LOG_DIR = Path(env("LOG_DIR", default=str(BASE_DIR / "logs")))
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_LEVEL = env("LOG_LEVEL", default="INFO")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {"format": "{asctime} {levelname} {name} {message}", "style": "{"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "standard"},
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(LOG_DIR / "app.log"),
            "maxBytes": 5 * 1024 * 1024,
            "backupCount": 5,
            "encoding": "utf-8",
            "formatter": "standard",
        },
    },
    "loggers": {
        "django": {"handlers": ["console", "file"], "level": LOG_LEVEL, "propagate": False},
        "django.security": {"handlers": ["console", "file"], "level": "WARNING", "propagate": False},
        "apps": {"handlers": ["console", "file"], "level": LOG_LEVEL, "propagate": False},
    },
}
