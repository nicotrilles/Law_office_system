from io import StringIO
from unittest import mock

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db.utils import OperationalError
from django.test import Client, TestCase, override_settings


class HomeAndHealthTests(TestCase):
    def test_home_page_renders(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Jumamil Law System")

    def test_health_ok_reports_only_status(self):
        response = self.client.get("/health/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_health_returns_503_without_leaking_details_when_database_is_down(self):
        with mock.patch(
            "apps.core.views.connection.cursor",
            side_effect=OperationalError("password authentication failed for jumamil_app"),
        ):
            response = self.client.get("/health/")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {"status": "unavailable"})
        self.assertNotIn("jumamil_app", response.content.decode())

    def test_health_rejects_post(self):
        self.assertEqual(self.client.post("/health/").status_code, 405)


class ErrorPageTests(TestCase):
    def test_404_uses_custom_template_and_shows_no_debug_information(self):
        response = self.client.get("/does-not-exist/")
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, "errors/404.html")
        self.assertNotIn("Traceback", response.content.decode())

    def test_csrf_failure_returns_generic_403_page(self):
        client = Client(enforce_csrf_checks=True)
        response = client.post("/")
        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed(response, "errors/403.html")

    @override_settings(ROOT_URLCONF="apps.core.tests.urls_for_tests", DEBUG=False)
    def test_500_page_hides_the_internal_error_message(self):
        client = Client(raise_request_exception=False)
        with self.assertLogs("django.request", level="ERROR"):
            response = client.get("/boom/")
        self.assertEqual(response.status_code, 500)
        body = response.content.decode()
        self.assertIn("Something went wrong", body)
        self.assertNotIn("SECRET-INTERNAL-DETAIL", body)
        self.assertNotIn("Traceback", body)


class CheckDatabaseCommandTests(TestCase):
    def test_reports_success_and_never_prints_the_password(self):
        out = StringIO()
        call_command("check_database", stdout=out)
        text = out.getvalue()
        self.assertIn("Connection OK", text)
        self.assertIn("PostgreSQL version", text)
        password = settings.DATABASES["default"]["PASSWORD"]
        self.assertTrue(password)
        self.assertNotIn(password, text)

    def test_failure_gives_a_clear_message_without_the_password(self):
        with mock.patch(
            "apps.core.management.commands.check_database.connection.ensure_connection",
            side_effect=OperationalError("could not connect"),
        ):
            with self.assertLogs("apps.core.management.commands.check_database", level="ERROR"):
                with self.assertRaises(CommandError) as ctx:
                    call_command("check_database", stdout=StringIO())
        self.assertIn("Could not connect", str(ctx.exception))
        self.assertNotIn(settings.DATABASES["default"]["PASSWORD"], str(ctx.exception))
