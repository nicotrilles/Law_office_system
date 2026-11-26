"""The permission lookup: has_permission() and get_permission_keys()."""
import ast
from pathlib import Path
from unittest import mock

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ImproperlyConfigured
from django.db.utils import OperationalError
from django.test import TestCase

from apps.accounts import permissions, reference_data
from apps.accounts.models import Permission, Role, RolePermission, User
from apps.accounts.permissions import PermissionLookupError, get_permission_keys, has_permission

PASSWORD = "correct-horse-battery-staple"
ALL_KEYS = ("client.view", "client.create", "client.edit")


class PermissionTestCase(TestCase):
    def setUp(self):
        reference_data.sync_roles()
        reference_data.sync_permissions()
        self.staff_role = Role.objects.get(role_name="Office Staff")
        self.attorney_role = Role.objects.get(role_name="Attorney")
        self.staff = User.objects.create_user("staffer", "Sam Staff", self.staff_role, PASSWORD)
        self.attorney = User.objects.create_user("attorney1", "Atty Jumamil", self.attorney_role, PASSWORD)

    def grant(self, role, key):
        RolePermission.objects.create(role=role, permission=Permission.objects.get(permission_key=key))

    def fresh(self, user):
        """A new user object, like the one a NEW request loads."""
        return User.objects.get(pk=user.pk)


class LookupTests(PermissionTestCase):
    def test_without_assignments_nobody_holds_anything(self):
        self.assertEqual(get_permission_keys(self.staff), frozenset())
        for key in ALL_KEYS:
            self.assertFalse(has_permission(self.staff, key))
            self.assertFalse(has_permission(self.attorney, key))

    def test_assigned_permissions_are_returned(self):
        self.grant(self.staff_role, "client.view")
        self.grant(self.staff_role, "client.create")
        user = self.fresh(self.staff)
        self.assertEqual(get_permission_keys(user), frozenset({"client.view", "client.create"}))
        self.assertTrue(has_permission(user, "client.view"))
        self.assertFalse(has_permission(user, "client.edit"))

    def test_different_roles_hold_different_permissions(self):
        for key in ALL_KEYS:
            self.grant(self.staff_role, key)
        self.grant(self.attorney_role, "client.view")  # the confirmed initial matrix
        staff, attorney = self.fresh(self.staff), self.fresh(self.attorney)
        self.assertEqual(get_permission_keys(staff), frozenset(ALL_KEYS))
        self.assertEqual(get_permission_keys(attorney), frozenset({"client.view"}))
        self.assertFalse(has_permission(attorney, "client.create"))
        self.assertFalse(has_permission(attorney, "client.edit"))

    def test_anonymous_users_hold_nothing_and_cost_no_query(self):
        with self.assertNumQueries(0):
            self.assertEqual(get_permission_keys(AnonymousUser()), frozenset())
            self.assertFalse(has_permission(AnonymousUser(), "client.view"))

    def test_inactive_users_hold_nothing_even_with_assignments(self):
        self.grant(self.staff_role, "client.view")
        User.objects.filter(pk=self.staff.pk).update(account_status="inactive")
        user = self.fresh(self.staff)
        with self.assertNumQueries(0):
            self.assertEqual(get_permission_keys(user), frozenset())
            self.assertFalse(has_permission(user, "client.view"))

    def test_an_unknown_key_raises_and_never_grants(self):
        self.grant(self.staff_role, "client.view")
        user = self.fresh(self.staff)
        with self.assertNumQueries(0):
            with self.assertRaises(ImproperlyConfigured):
                has_permission(user, "client.vew")

    def test_registry_keys_are_the_three_approved_ones(self):
        self.assertEqual(permissions.known_permission_keys(), set(ALL_KEYS))


class CachingAndChangeTests(PermissionTestCase):
    def test_repeated_checks_within_one_request_use_one_query(self):
        self.grant(self.staff_role, "client.view")
        user = self.fresh(self.staff)
        with self.assertNumQueries(1):
            for _ in range(5):
                has_permission(user, "client.view")
                has_permission(user, "client.edit")

    def test_grants_and_revokes_take_effect_on_the_next_request(self):
        stale = self.fresh(self.staff)
        self.assertFalse(has_permission(stale, "client.view"))
        self.grant(self.staff_role, "client.view")
        self.assertFalse(has_permission(stale, "client.view"))          # same request: answer was remembered
        self.assertTrue(has_permission(self.fresh(self.staff), "client.view"))   # next request: new answer
        RolePermission.objects.all().delete()
        self.assertFalse(has_permission(self.fresh(self.staff), "client.view"))


class LookupFailureTests(PermissionTestCase):
    def test_a_failed_lookup_raises_it_is_not_reported_as_no_permission(self):
        self.grant(self.staff_role, "client.view")
        user = self.fresh(self.staff)
        with mock.patch.object(permissions, "_load_keys", side_effect=OperationalError("connection lost")):
            with self.assertLogs("apps.accounts.permissions", level="ERROR") as logs:
                with self.assertRaises(PermissionLookupError):
                    has_permission(user, "client.view")
        self.assertIn(f"user_id={user.pk}", " ".join(logs.output))
        self.assertNotIn("staffer", " ".join(logs.output))  # no username in the log

    def test_get_permission_keys_also_raises_instead_of_returning_an_empty_set(self):
        user = self.fresh(self.staff)
        with mock.patch.object(permissions, "_load_keys", side_effect=OperationalError("x")):
            with self.assertLogs("apps.accounts.permissions", level="ERROR"):
                with self.assertRaises(PermissionLookupError):
                    get_permission_keys(user)

    def test_the_failure_is_remembered_for_the_rest_of_the_request_without_retrying(self):
        user = self.fresh(self.staff)
        with mock.patch.object(permissions, "_load_keys", side_effect=OperationalError("x")) as load:
            with self.assertLogs("apps.accounts.permissions", level="ERROR"):
                for _ in range(3):
                    with self.assertRaises(PermissionLookupError):
                        has_permission(user, "client.view")
        self.assertEqual(load.call_count, 1)

    def test_a_new_request_is_not_poisoned_by_an_earlier_failure(self):
        self.grant(self.staff_role, "client.view")
        with mock.patch.object(permissions, "_load_keys", side_effect=OperationalError("x")):
            with self.assertLogs("apps.accounts.permissions", level="ERROR"):
                with self.assertRaises(PermissionLookupError):
                    has_permission(self.fresh(self.staff), "client.view")
        self.assertTrue(has_permission(self.fresh(self.staff), "client.view"))


class DesignRuleTests(PermissionTestCase):
    def source_tree(self, name):
        return ast.parse((Path(settings.BASE_DIR) / "apps" / "accounts" / name).read_text(encoding="utf-8"))

    def test_no_role_name_comparisons_and_no_django_permission_machinery(self):
        forbidden_strings = {"Attorney", "Office Staff"}
        forbidden_attributes = {"role_name", "is_superuser", "is_staff", "has_perm", "has_perms",
                                "user_permissions", "groups"}
        for module in ("permissions.py", "decorators.py"):
            for node in ast.walk(self.source_tree(module)):
                if isinstance(node, ast.Constant) and isinstance(node.value, str):
                    self.assertNotIn(node.value, forbidden_strings, module)
                if isinstance(node, ast.Attribute):
                    self.assertNotIn(node.attr, forbidden_attributes, module)

    def test_there_is_no_superuser_bypass(self):
        user = self.fresh(self.attorney)
        user.is_superuser = True  # such a flag must have no effect at all
        user.is_staff = True
        self.assertFalse(has_permission(user, "client.edit"))
