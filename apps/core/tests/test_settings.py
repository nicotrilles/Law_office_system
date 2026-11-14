"""Guards for the foundation decisions (custom user model, hashing, sessions, secrets)."""
import os
import subprocess
import sys
from pathlib import Path

from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase

BASE_DIR = Path(settings.BASE_DIR)


def _run_settings_import(module, extra_env, drop=()):
    """Import a settings module in a clean subprocess and return the finished process."""
    env = {k: v for k, v in os.environ.items() if k not in drop}
    env["DJANGO_ENV_FILE"] = str(BASE_DIR / "does-not-exist.env")  # ignore the real .env
    env.update(extra_env)
    return subprocess.run(
        [sys.executable, "-c", f"import importlib; importlib.import_module('{module}')"],
        cwd=BASE_DIR, env=env, capture_output=True, text=True,
    )


class CustomUserModelTests(SimpleTestCase):
    def test_custom_user_model_is_configured(self):
        self.assertEqual(settings.AUTH_USER_MODEL, "accounts.User")
        self.assertIs(get_user_model(), apps.get_model("accounts", "User"))

    def test_django_admin_is_not_installed(self):
        self.assertNotIn("django.contrib.admin", settings.INSTALLED_APPS)


class SecuritySettingsTests(SimpleTestCase):
    def test_argon2_is_the_only_password_hasher(self):
        self.assertEqual(
            settings.PASSWORD_HASHERS, ["django.contrib.auth.hashers.Argon2PasswordHasher"]
        )

    def test_minimum_password_length_follows_the_setting(self):
        validators = {v["NAME"].rsplit(".", 1)[-1]: v for v in settings.AUTH_PASSWORD_VALIDATORS}
        options = validators["MinimumLengthValidator"]["OPTIONS"]
        self.assertEqual(options["min_length"], settings.PASSWORD_MIN_LENGTH)
        self.assertGreaterEqual(settings.PASSWORD_MIN_LENGTH, 12)

    def test_session_cookie_hardening(self):
        self.assertTrue(settings.SESSION_COOKIE_HTTPONLY)
        self.assertEqual(settings.SESSION_COOKIE_SAMESITE, "Lax")
        self.assertTrue(settings.SESSION_SAVE_EVERY_REQUEST)
        self.assertTrue(settings.SESSION_EXPIRE_AT_BROWSER_CLOSE)
        self.assertEqual(settings.SESSION_COOKIE_AGE, settings.SESSION_IDLE_TIMEOUT_SECONDS)

    def test_clickjacking_and_sniffing_protection(self):
        self.assertEqual(settings.X_FRAME_OPTIONS, "DENY")
        self.assertTrue(settings.SECURE_CONTENT_TYPE_NOSNIFF)

    def test_document_storage_is_not_under_a_served_static_folder(self):
        storage = Path(settings.DOCUMENT_STORAGE_ROOT).resolve()
        served = [Path(p).resolve() for p in settings.STATICFILES_DIRS] + [
            Path(settings.STATIC_ROOT).resolve()
        ]
        for folder in served:
            self.assertNotIn(folder, [storage, *storage.parents])
            self.assertNotIn(storage, [folder, *folder.parents])
        # No public media folder is configured anywhere: documents are never served directly.
        self.assertEqual(settings.MEDIA_ROOT, "")


class SecretsAndEnvironmentTests(SimpleTestCase):
    def test_app_refuses_to_start_without_a_secret_key(self):
        result = _run_settings_import(
            "config.settings.dev",
            {"DATABASE_URL": "postgres://u:p@localhost:5432/x"},
            drop=("SECRET_KEY",),
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("SECRET_KEY", result.stderr)

    def test_production_settings_require_allowed_hosts(self):
        result = _run_settings_import(
            "config.settings.prod",
            {"SECRET_KEY": "x" * 50, "DATABASE_URL": "postgres://u:p@localhost:5432/x"},
            drop=("ALLOWED_HOSTS",),
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("ALLOWED_HOSTS", result.stderr)

    def test_production_defaults_to_secure_cookies_and_https_redirect(self):
        code = (
            "import importlib;m=importlib.import_module('config.settings.prod');"
            "print(m.DEBUG, m.SESSION_COOKIE_SECURE, m.CSRF_COOKIE_SECURE, m.SECURE_SSL_REDIRECT)"
        )
        env = {k: v for k, v in os.environ.items()
               if k not in ("SESSION_COOKIE_SECURE", "CSRF_COOKIE_SECURE", "SECURE_SSL_REDIRECT")}
        env.update({"DJANGO_ENV_FILE": str(BASE_DIR / "nope.env"), "SECRET_KEY": "x" * 50,
                    "DATABASE_URL": "postgres://u:p@localhost:5432/x", "ALLOWED_HOSTS": "example.org"})
        result = subprocess.run([sys.executable, "-c", code], cwd=BASE_DIR, env=env,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "False True True True")


class MigrationStateTests(TestCase):
    def test_models_and_migrations_are_in_sync(self):
        # Fails (SystemExit) if a model changed without a matching migration file.
        call_command("makemigrations", "--check", "--dry-run", verbosity=0)
