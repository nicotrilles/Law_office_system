"""Failed-login throttling. Uses the real PostgreSQL-backed cache and a fake clock."""
import re
from unittest import mock

from django.db import connection
from django.db.utils import ProgrammingError
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.accounts import forms, throttle
from apps.accounts.models import Role, User

PASSWORD = "correct-horse-battery-staple"
WRONG = "Wrong-Pass-Secret-1"


@override_settings(LOGIN_MAX_ATTEMPTS=3, LOGIN_LOCKOUT_MINUTES=10)
class ThrottleTestCase(TestCase):
    def setUp(self):
        self.role = Role.objects.create(role_name="Office Staff")
        self.user = User.objects.create_user("maria", "Maria Santos", self.role, PASSWORD)
        self.url = reverse("accounts:login")
        self.clock = [1_000_000.0]  # the throttle's own clock; the cache's real expiry is only housekeeping
        patcher = mock.patch.object(throttle, "now", side_effect=lambda: self.clock[0])
        patcher.start()
        self.addCleanup(patcher.stop)

    def advance(self, seconds):
        self.clock[0] += seconds

    def attempt(self, username="maria", password=PASSWORD, address="10.0.0.1", **extra):
        return self.client.post(self.url, {"username": username, "password": password},
                                REMOTE_ADDR=address, **extra)

    def errors(self, response):
        return list(response.context["form"].non_field_errors())

    def fail(self, times, username="maria", address="10.0.0.1"):
        return [self.errors(self.attempt(username, WRONG, address)) for _ in range(times)]

    def signed_in(self):
        return "_auth_user_id" in self.client.session


class LockoutTests(ThrottleTestCase):
    def test_the_throttle_table_exists_in_a_fresh_test_database(self):
        # Django creates every database cache table when it builds the test database.
        self.assertIn("login_throttle_cache", connection.introspection.table_names())

    def test_the_nth_failure_locks_and_the_correct_password_is_then_refused(self):
        for messages in self.fail(3):
            self.assertEqual(messages, [forms.GENERIC_LOGIN_ERROR])
        response = self.attempt(password=PASSWORD)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.errors(response), [forms.locked_error()])
        self.assertFalse(self.signed_in())

    def test_the_lock_message_is_identical_for_real_and_unknown_usernames(self):
        real_failures = self.fail(3, "maria")
        unknown_failures = self.fail(3, "nobody")
        self.assertEqual(real_failures, unknown_failures)  # same generic message while counting
        self.assertEqual(self.errors(self.attempt("maria")), self.errors(self.attempt("nobody")))
        self.assertEqual(self.errors(self.attempt("nobody")), [forms.locked_error()])

    def test_inactive_accounts_are_counted_like_any_other(self):
        User.objects.filter(pk=self.user.pk).update(account_status="inactive")
        self.fail(3)
        self.assertEqual(self.errors(self.attempt()), [forms.locked_error()])

    def test_the_password_is_not_checked_while_locked(self):
        self.fail(3)
        with mock.patch("django.contrib.auth.forms.authenticate") as authenticate:
            response = self.attempt()
        authenticate.assert_not_called()
        self.assertEqual(self.errors(response), [forms.locked_error()])

    def test_a_blank_password_is_not_counted(self):
        for _ in range(5):
            self.attempt(password="")
        with connection.cursor() as cursor:
            cursor.execute("SELECT count(*) FROM login_throttle_cache")
            self.assertEqual(cursor.fetchone()[0], 0)


class TimingTests(ThrottleTestCase):
    def test_the_lock_ends_after_the_lockout_time(self):
        self.fail(3)
        self.advance(599)
        self.assertEqual(self.errors(self.attempt()), [forms.locked_error()])
        self.advance(2)  # 601 seconds after the lock started
        self.assertEqual(self.attempt().status_code, 302)
        self.assertTrue(self.signed_in())

    def test_later_attempts_do_not_extend_the_lock(self):
        self.fail(3)                      # lock starts at t = 0 and ends at t = 600
        self.advance(300)
        self.attempt()                    # refused. It must NOT push the end past t = 600
        self.advance(301)                 # t = 601
        self.assertEqual(self.attempt().status_code, 302)

    def test_the_failure_window_is_fixed_and_restarts_after_it_expires(self):
        self.fail(2)
        self.advance(601)                 # the fixed window has ended, so counting starts again
        self.fail(2)                      # only 2 failures in the new window: not locked
        self.assertEqual(self.attempt().status_code, 302)

    @override_settings(LOGIN_MAX_ATTEMPTS=2, LOGIN_LOCKOUT_MINUTES=1)
    def test_both_settings_are_honoured(self):
        self.fail(2)
        response = self.attempt()
        self.assertEqual(self.errors(response), ["Too many failed sign-in attempts. Please wait 1 minute and try again."])
        self.advance(61)
        self.assertEqual(self.attempt().status_code, 302)


class CountingTests(ThrottleTestCase):
    def test_a_successful_sign_in_clears_the_count(self):
        self.fail(2)
        self.assertEqual(self.attempt().status_code, 302)
        self.client.logout()
        self.fail(2)                      # 2 + 2 would lock if the first 2 had not been cleared
        self.assertEqual(self.attempt().status_code, 302)

    def test_letter_case_does_not_create_separate_counters(self):
        for name in ("maria", "MARIA", "Maria"):
            self.attempt(name, WRONG)
        self.assertEqual(self.errors(self.attempt("maria")), [forms.locked_error()])

    def test_a_different_network_address_is_counted_separately(self):
        self.fail(3, address="10.0.0.1")
        self.assertEqual(self.attempt(address="10.0.0.2").status_code, 302)

    def test_forwarded_address_headers_cannot_dodge_the_lock(self):
        for i in range(3):
            self.attempt(password=WRONG, HTTP_X_FORWARDED_FOR=f"203.0.113.{i}")
        response = self.attempt(HTTP_X_FORWARDED_FOR="198.51.100.77")
        self.assertEqual(self.errors(response), [forms.locked_error()])


class StorageAndSafetyTests(ThrottleTestCase):
    def test_counters_live_in_postgresql_under_hashed_keys(self):
        self.attempt(password=WRONG)
        with connection.cursor() as cursor:
            cursor.execute("SELECT cache_key FROM login_throttle_cache")
            keys = [row[0] for row in cursor.fetchall()]
        self.assertEqual(len(keys), 1)
        self.assertRegex(keys[0], r"login:[0-9a-f]{64}$")
        self.assertNotIn("maria", keys[0])
        self.assertNotIn("10.0.0.1", keys[0])

    def test_logs_never_contain_the_username_or_the_password(self):
        with self.assertLogs("apps.accounts.throttle", level="WARNING") as logs:
            self.fail(3)
        text = " ".join(logs.output)
        self.assertIn("lockout started", text)
        for secret in ("maria", WRONG, "10.0.0.1"):
            self.assertNotIn(secret, text)

    def test_sign_in_fails_closed_when_the_store_is_unavailable(self):
        with mock.patch("django.core.cache.backends.db.DatabaseCache.get",
                        side_effect=ProgrammingError("relation does not exist")):
            with self.assertLogs("apps.accounts.throttle", level="ERROR") as logs:
                response = self.attempt(password=PASSWORD)  # even the CORRECT password
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.errors(response), [forms.UNAVAILABLE_ERROR])
        self.assertFalse(self.signed_in())
        self.assertIn("createcachetable", " ".join(logs.output))
