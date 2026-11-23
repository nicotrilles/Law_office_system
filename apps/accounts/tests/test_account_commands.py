"""setup_attorney and create_user."""
import threading
from io import StringIO
from unittest import mock

from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connections
from django.db.utils import ProgrammingError
from django.test import TestCase, TransactionTestCase

from apps.accounts import reference_data
from apps.accounts.management import prompts
from apps.accounts.models import Permission, Role, RolePermission, User

GOOD = "Violet-Harbor-Lantern-77"


class CommandTestCase(TestCase):
    """Simulates an interactive terminal and the hidden password prompt."""

    def setUp(self):
        interactive = mock.patch.object(prompts, "_stdin_is_interactive", return_value=True)
        interactive.start()
        self.addCleanup(interactive.stop)

    def run_command(self, name, passwords=(GOOD, GOOD), username="drjumamil", full_name="Atty. Jumamil", extra=()):
        args = ["--username", username, "--full-name", full_name, *extra]
        out, err = StringIO(), StringIO()
        with mock.patch("getpass.getpass", side_effect=list(passwords)) as hidden:
            self.hidden = hidden  # recorded first, so it is correct even when the command refuses
            call_command(name, *args, stdout=out, stderr=err)
        return out.getvalue(), err.getvalue()

    def assertFails(self, name, message_part=None, **kwargs):
        with self.assertRaises(CommandError) as ctx:
            self.run_command(name, **kwargs)
        if message_part:
            self.assertIn(message_part, str(ctx.exception))
        return ctx.exception


class SetupAttorneyTests(CommandTestCase):
    def test_creates_one_active_attorney_with_a_hashed_password(self):
        out, err = self.run_command("setup_attorney")
        user = User.objects.get(username="drjumamil")
        self.assertEqual(user.role.role_name, "Attorney")
        self.assertEqual(user.account_status, "active")
        self.assertTrue(user.password.startswith("argon2$"))
        self.assertTrue(user.check_password(GOOD))
        self.assertIn('Created Attorney account "drjumamil"', out)

    def test_password_is_prompted_twice_hidden_and_never_printed(self):
        out, err = self.run_command("setup_attorney")
        self.assertEqual(self.hidden.call_count, 2)
        self.assertNotIn(GOOD, out + err)

    def test_it_creates_the_roles_and_assigns_no_permissions(self):
        self.run_command("setup_attorney")
        self.assertEqual(set(Role.objects.values_list("role_name", flat=True)), {"Office Staff", "Attorney"})
        self.assertEqual(Permission.objects.count(), 0)
        self.assertEqual(RolePermission.objects.count(), 0)

    def test_it_asks_for_username_and_full_name_when_not_given(self):
        with mock.patch("builtins.input", side_effect=["drjumamil", "Atty. Jumamil"]):
            with mock.patch("getpass.getpass", side_effect=[GOOD, GOOD]):
                call_command("setup_attorney", stdout=StringIO(), stderr=StringIO())
        self.assertTrue(User.objects.filter(username="drjumamil").exists())

    def test_a_weak_password_and_a_mismatch_are_rejected_and_asked_again(self):
        out, err = self.run_command("setup_attorney", passwords=("short", "short", GOOD, "different", GOOD, GOOD))
        self.assertIn("too short", err)
        self.assertIn("do not match", err)
        self.assertTrue(User.objects.get(username="drjumamil").check_password(GOOD))

    def test_a_password_too_similar_to_the_username_is_rejected(self):
        with self.assertRaises(CommandError):
            self.run_command("setup_attorney", passwords=("drjumamil2026", "drjumamil2026") * 3)
        self.assertFalse(User.objects.exists())

    def test_three_bad_attempts_abort_and_create_nothing(self):
        self.assertFails("setup_attorney", "Nothing was created", passwords=("short", "short") * 3)
        self.assertFalse(User.objects.exists())

    def test_a_second_run_is_refused_without_asking_for_a_password(self):
        self.run_command("setup_attorney")
        self.assertFails("setup_attorney", "already exists", username="another")
        self.assertEqual(self.hidden.call_count, 0)
        self.assertEqual(User.objects.filter(role__role_name="Attorney").count(), 1)

    def test_an_inactive_attorney_still_blocks_a_second_run(self):
        self.run_command("setup_attorney")
        User.objects.filter(username="drjumamil").update(account_status="inactive")
        self.assertFails("setup_attorney", "already exists", username="another")
        self.assertEqual(User.objects.filter(role__role_name="Attorney").count(), 1)

    def test_username_and_full_name_are_validated(self):
        self.assertFails("setup_attorney", "cannot be empty", username="   ")
        self.assertFails("setup_attorney", "too long", username="a" * 51)
        self.assertFails("setup_attorney", "too long", full_name="n" * 151)
        self.assertFalse(User.objects.exists())

    def test_the_length_limits_match_the_model_and_the_boundary_is_accepted(self):
        self.assertEqual(User._meta.get_field("username").max_length, 50)
        self.assertEqual(User._meta.get_field("full_name").max_length, 150)
        self.run_command("setup_attorney", username="a" * 50, full_name="n" * 150)
        self.assertTrue(User.objects.filter(username="a" * 50).exists())

    def test_a_username_in_use_is_refused_in_any_letter_case(self):
        staff = Role.objects.create(role_name="Office Staff")
        User.objects.create_user("Drjumamil", "Someone", staff, GOOD)
        self.assertFails("setup_attorney", "already in use")

    def test_non_interactive_input_is_refused(self):
        with mock.patch.object(prompts, "_stdin_is_interactive", return_value=False):
            self.assertFails("setup_attorney", "interactive terminal")
        self.assertFalse(User.objects.exists())

    def test_a_role_differing_only_in_capitals_stops_the_command(self):
        Role.objects.create(role_name="attorney")
        self.assertFails("setup_attorney", "capital letters")
        self.assertFalse(User.objects.exists())

    def test_unmigrated_database_gives_a_friendly_error(self):
        with mock.patch.object(reference_data, "sync_roles", side_effect=ProgrammingError("no table")):
            with self.assertLogs("apps.accounts.management.commands.setup_attorney", level="ERROR"):
                self.assertFails("setup_attorney", "migrate")


class CreateUserTests(CommandTestCase):
    def test_creates_an_active_office_staff_account_with_a_hashed_password(self):
        out, err = self.run_command("create_user", username="maria", full_name="Maria Santos")
        user = User.objects.get(username="maria")
        self.assertEqual(user.role.role_name, "Office Staff")
        self.assertEqual(user.account_status, "active")
        self.assertTrue(user.password.startswith("argon2$"))
        self.assertNotIn(GOOD, out + err)
        self.assertEqual(self.hidden.call_count, 2)

    def test_it_assigns_no_permissions(self):
        self.run_command("create_user", username="maria", full_name="Maria Santos")
        self.assertEqual(Permission.objects.count(), 0)
        self.assertEqual(RolePermission.objects.count(), 0)

    def test_it_cannot_create_an_attorney(self):
        with self.assertRaises(CommandError):
            self.run_command("create_user", username="sneaky", full_name="Sneaky", extra=("--role", "Attorney"))
        self.assertFalse(User.objects.filter(role__role_name="Attorney").exists())
        self.assertFalse(User.objects.filter(username="sneaky").exists())

    def test_it_works_with_and_without_an_attorney_present(self):
        self.run_command("setup_attorney")
        self.run_command("create_user", username="maria", full_name="Maria Santos")
        self.assertEqual(User.objects.filter(role__role_name="Attorney").count(), 1)
        self.assertEqual(User.objects.filter(role__role_name="Office Staff").count(), 1)

    def test_duplicate_usernames_are_refused_in_any_letter_case_even_the_attorneys(self):
        self.run_command("setup_attorney", username="DrJumamil")
        self.assertFails("create_user", "already in use", username="drjumamil")

    def test_weak_passwords_are_re_asked_and_three_failures_abort(self):
        self.run_command("create_user", username="maria", full_name="Maria Santos", passwords=("short", "short", GOOD, GOOD))
        self.assertTrue(User.objects.filter(username="maria").exists())
        self.assertFails("create_user", "Nothing was created", username="ivan", passwords=("short", "short") * 3)
        self.assertFalse(User.objects.filter(username="ivan").exists())

    def test_input_is_validated_and_non_interactive_is_refused(self):
        self.assertFails("create_user", "too long", username="a" * 51)
        self.assertFails("create_user", "cannot be empty", full_name=" ")
        with mock.patch.object(prompts, "_stdin_is_interactive", return_value=False):
            self.assertFails("create_user", "interactive terminal")
        self.assertFalse(User.objects.exists())


class SetupAttorneyConcurrencyTests(TransactionTestCase):
    """Two real database connections: only one of two simultaneous runs may create the Attorney."""

    def test_two_simultaneous_runs_create_only_one_attorney(self):
        reference_data.sync_roles()
        barrier = threading.Barrier(2)
        results = []

        def run(username):
            try:
                barrier.wait(timeout=10)
                call_command("setup_attorney", "--username", username, "--full-name", "Atty",
                             stdout=StringIO(), stderr=StringIO())
                results.append("created")
            except CommandError:
                results.append("refused")
            except Exception as exc:  # anything else is a failure of the test
                results.append(repr(exc))
            finally:
                connections.close_all()

        with mock.patch.object(prompts, "_stdin_is_interactive", return_value=True), \
                mock.patch("getpass.getpass", return_value=GOOD):
            threads = [threading.Thread(target=run, args=(name,)) for name in ("atty_one", "atty_two")]
            for t in threads:
                t.start()
            for t in threads:
                t.join(timeout=60)

        self.assertEqual(sorted(results), ["created", "refused"])
        self.assertEqual(User.objects.filter(role__role_name="Attorney").count(), 1)
