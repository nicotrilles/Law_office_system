"""manage.py role_permissions list | grant | revoke"""
import re
from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from apps.accounts import reference_data
from apps.accounts.models import Permission, Role, RolePermission


class RolePermissionsTestCase(TestCase):
    def setUp(self):
        reference_data.sync_roles()
        reference_data.sync_permissions()

    def run_cmd(self, *args):
        out = StringIO()
        call_command("role_permissions", *args, stdout=out)
        return out.getvalue()

    def grant(self, role, key):
        return self.run_cmd("grant", "--role", role, "--permission", key)

    def pairs(self):
        return {(rp.role.role_name, rp.permission.permission_key) for rp in RolePermission.objects.select_related("role", "permission")}


class GrantTests(RolePermissionsTestCase):
    def test_nothing_is_assigned_until_a_grant_is_made(self):
        self.assertEqual(RolePermission.objects.count(), 0)

    def test_grant_creates_the_assignment_and_logs_it(self):
        with self.assertLogs("apps.accounts.management.commands.role_permissions", level="INFO") as logs:
            text = self.grant("Office Staff", "client.view")
        self.assertIn("Granted client.view to Office Staff.", text)
        self.assertEqual(self.pairs(), {("Office Staff", "client.view")})
        self.assertIn("role=Office Staff permission=client.view", " ".join(logs.output))

    def test_granting_twice_is_harmless(self):
        self.grant("Office Staff", "client.view")
        text = self.grant("Office Staff", "client.view")
        self.assertIn("already holds client.view. No change.", text)
        self.assertEqual(RolePermission.objects.count(), 1)

    def test_an_unknown_role_is_refused_and_the_error_lists_the_roles(self):
        with self.assertRaises(CommandError) as ctx:
            self.grant("Receptionist", "client.view")
        self.assertIn("Attorney, Office Staff", str(ctx.exception))
        self.assertEqual(RolePermission.objects.count(), 0)

    def test_a_key_that_is_not_defined_is_refused(self):
        with self.assertRaises(CommandError) as ctx:
            self.grant("Office Staff", "client.delete")
        self.assertIn("not a defined permission", str(ctx.exception))
        self.assertIn("client.view", str(ctx.exception))

    def test_a_defined_but_unseeded_key_tells_you_to_seed(self):
        Permission.objects.filter(permission_key="client.edit").delete()
        with self.assertRaises(CommandError) as ctx:
            self.grant("Office Staff", "client.edit")
        self.assertIn("seed_reference_data", str(ctx.exception))

    def test_a_permission_that_is_not_in_the_registry_cannot_be_granted(self):
        Permission.objects.create(permission_key="old.key", module="old")
        with self.assertRaises(CommandError):
            self.grant("Office Staff", "old.key")


class RevokeTests(RolePermissionsTestCase):
    def test_revoke_removes_the_assignment_and_logs_it(self):
        self.grant("Office Staff", "client.view")
        with self.assertLogs("apps.accounts.management.commands.role_permissions", level="INFO") as logs:
            text = self.run_cmd("revoke", "--role", "Office Staff", "--permission", "client.view")
        self.assertIn("Revoked client.view from Office Staff.", text)
        self.assertEqual(RolePermission.objects.count(), 0)
        self.assertIn("Permission revoked", " ".join(logs.output))

    def test_revoking_something_not_held_is_harmless(self):
        text = self.run_cmd("revoke", "--role", "Attorney", "--permission", "client.create")
        self.assertIn("did not hold client.create. No change.", text)

    def test_revoke_only_touches_the_named_role(self):
        self.grant("Office Staff", "client.view")
        self.grant("Attorney", "client.view")
        self.run_cmd("revoke", "--role", "Office Staff", "--permission", "client.view")
        self.assertEqual(self.pairs(), {("Attorney", "client.view")})

    def test_unknown_role_or_permission_is_refused(self):
        with self.assertRaises(CommandError):
            self.run_cmd("revoke", "--role", "Nobody", "--permission", "client.view")
        with self.assertRaises(CommandError) as ctx:
            self.run_cmd("revoke", "--role", "Attorney", "--permission", "client.nope")
        self.assertIn("No permission", str(ctx.exception))

    def test_a_permission_removed_from_the_registry_can_still_be_revoked(self):
        orphan = Permission.objects.create(permission_key="old.key", module="old")
        RolePermission.objects.create(role=Role.objects.get(role_name="Attorney"), permission=orphan)
        self.run_cmd("revoke", "--role", "Attorney", "--permission", "old.key")
        self.assertEqual(RolePermission.objects.count(), 0)


class ListAndMatrixTests(RolePermissionsTestCase):
    def apply_matrix(self):
        for key in ("client.view", "client.create", "client.edit"):
            self.grant("Office Staff", key)
        self.grant("Attorney", "client.view")

    def test_the_confirmed_initial_matrix_is_exactly_four_assignments(self):
        self.apply_matrix()
        self.assertEqual(self.pairs(), {
            ("Office Staff", "client.view"), ("Office Staff", "client.create"), ("Office Staff", "client.edit"),
            ("Attorney", "client.view"),
        })

    def test_list_shows_the_matrix(self):
        self.apply_matrix()
        text = self.run_cmd("list")
        self.assertRegex(text, r"Permission\s+Attorney\s+Office Staff")
        self.assertRegex(text, r"client\.view\s+yes\s+yes")
        self.assertRegex(text, r"client\.create\s+-\s+yes")
        self.assertRegex(text, r"client\.edit\s+-\s+yes")

    def test_list_with_nothing_granted_shows_no_yes(self):
        self.assertNotIn("yes", self.run_cmd("list"))

    def test_list_is_read_only(self):
        self.run_cmd("list")
        self.assertEqual(RolePermission.objects.count(), 0)

    def test_list_flags_unseeded_and_unregistered_permissions(self):
        Permission.objects.filter(permission_key="client.edit").delete()
        Permission.objects.create(permission_key="old.key", module="old")
        text = self.run_cmd("list")
        self.assertRegex(text, r"client\.edit.*NOT SEEDED")
        self.assertRegex(text, r"old\.key.*not in the registry")


class SeedInteractionTests(RolePermissionsTestCase):
    def test_reseeding_keeps_existing_assignments_and_adds_none(self):
        self.grant("Attorney", "client.view")
        call_command("seed_reference_data", stdout=StringIO())
        call_command("seed_reference_data", stdout=StringIO())
        self.assertEqual(self.pairs(), {("Attorney", "client.view")})

    def test_a_subcommand_is_required(self):
        with self.assertRaises(CommandError):
            call_command("role_permissions", stdout=StringIO(), stderr=StringIO())
