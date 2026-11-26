"""Tests for the reference data and the seed_reference_data command."""
import importlib
from io import StringIO
from unittest import mock

from django.core.management import call_command
from django.core.management.base import CommandError
from django.db.utils import ProgrammingError
from django.test import SimpleTestCase, TestCase

from apps.accounts import reference_data
from apps.accounts.models import Permission, Role, RolePermission, User


class RegistryTests(SimpleTestCase):
    def test_registry_holds_exactly_the_three_approved_definitions(self):
        definitions = {d.key: d for d in reference_data.PERMISSION_DEFINITIONS}
        self.assertEqual(set(definitions), {"client.view", "client.create", "client.edit"})
        self.assertEqual(len(reference_data.PERMISSION_DEFINITIONS), 3)
        for definition in definitions.values():
            self.assertEqual(definition.module, "clients")
            self.assertTrue(definition.description)

    def test_service_request_permissions_are_not_defined_yet(self):
        self.assertFalse([d for d in reference_data.PERMISSION_DEFINITIONS if d.key.startswith("request.")])

    def test_role_names_are_exactly_the_two_approved_roles(self):
        self.assertEqual(set(reference_data.ROLE_NAMES), {"Office Staff", "Attorney"})
        self.assertEqual(len(reference_data.ROLE_NAMES), 2)


class ImportTests(TestCase):
    def test_importing_reference_data_runs_no_database_queries(self):
        with self.assertNumQueries(0):
            importlib.reload(reference_data)


class SeedRolesTests(TestCase):
    def test_first_run_creates_both_roles(self):
        result = reference_data.sync_roles()
        self.assertEqual(set(result.created), {"Office Staff", "Attorney"})
        self.assertEqual(result.unchanged, [])
        self.assertEqual(set(Role.objects.values_list("role_name", flat=True)), {"Office Staff", "Attorney"})

    def test_second_run_changes_nothing(self):
        reference_data.sync_roles()
        ids = sorted(Role.objects.values_list("pk", flat=True))
        result = reference_data.sync_roles()
        self.assertEqual(result.created, [])
        self.assertEqual(set(result.unchanged), {"Office Staff", "Attorney"})
        self.assertEqual(sorted(Role.objects.values_list("pk", flat=True)), ids)

    def test_new_roles_have_no_description_and_existing_descriptions_are_kept(self):
        Role.objects.create(role_name="Attorney", description="kept as is")
        reference_data.sync_roles()
        self.assertEqual(Role.objects.get(role_name="Attorney").description, "kept as is")
        self.assertIsNone(Role.objects.get(role_name="Office Staff").description)

    def test_with_only_one_role_present_only_the_missing_one_is_created(self):
        Role.objects.create(role_name="Attorney")
        result = reference_data.sync_roles()
        self.assertEqual(result.created, ["Office Staff"])
        self.assertEqual(result.unchanged, ["Attorney"])

    def test_an_unrelated_role_is_not_changed_or_deleted(self):
        Role.objects.create(role_name="Clerk", description="untouched")
        reference_data.sync_roles()
        self.assertEqual(Role.objects.get(role_name="Clerk").description, "untouched")
        self.assertEqual(Role.objects.count(), 3)

    def test_a_role_differing_only_in_capitals_stops_the_seed_and_creates_nothing(self):
        Role.objects.create(role_name="attorney")
        with self.assertRaises(reference_data.RoleNameConflict):
            reference_data.sync_roles()
        self.assertEqual(set(Role.objects.values_list("role_name", flat=True)), {"attorney"})

    def test_seeding_creates_no_permissions_and_no_assignments(self):
        reference_data.sync_roles()
        reference_data.sync_roles()
        self.assertEqual(Permission.objects.count(), 0)
        self.assertEqual(RolePermission.objects.count(), 0)

    def test_seeding_does_not_touch_users(self):
        role = Role.objects.create(role_name="Clerk")
        User.objects.create_user("maria", "Maria Santos", role, "correct-horse-battery-staple")
        before = list(User.objects.values_list("pk", "username", "account_status"))
        reference_data.sync_roles()
        self.assertEqual(list(User.objects.values_list("pk", "username", "account_status")), before)


class SeedCommandTests(TestCase):
    def run_command(self):
        out = StringIO()
        call_command("seed_reference_data", stdout=out)
        return out.getvalue()

    def test_first_run_output(self):
        text = self.run_command()
        self.assertIn("Roles: 2 created, 0 unchanged.", text)
        self.assertIn("Permissions: 3 created, 0 updated, 0 unchanged.", text)
        self.assertIn("Role-permission assignments: untouched", text)
        self.assertEqual(RolePermission.objects.count(), 0)

    def test_second_run_output(self):
        self.run_command()
        text = self.run_command()
        self.assertIn("Roles: 0 created, 2 unchanged.", text)
        self.assertIn("Permissions: 0 created, 0 updated, 3 unchanged.", text)

    def test_capital_letter_conflict_gives_a_command_error(self):
        Role.objects.create(role_name="attorney")
        with self.assertRaises(CommandError) as ctx:
            self.run_command()
        self.assertIn("attorney", str(ctx.exception))

    def test_missing_tables_give_a_friendly_error(self):
        with mock.patch.object(reference_data, "sync_roles", side_effect=ProgrammingError("relation does not exist")):
            with self.assertLogs("apps.accounts.management.commands.seed_reference_data", level="ERROR"):
                with self.assertRaises(CommandError) as ctx:
                    self.run_command()
        self.assertIn("migrate", str(ctx.exception))


class SyncPermissionsTests(TestCase):
    def test_first_sync_creates_the_three_definitions_and_no_assignments(self):
        result = reference_data.sync_permissions()
        self.assertEqual(set(result.created), {"client.view", "client.create", "client.edit"})
        self.assertEqual(Permission.objects.count(), 3)
        self.assertEqual(set(Permission.objects.values_list("module", flat=True)), {"clients"})
        self.assertEqual(RolePermission.objects.count(), 0)

    def test_second_sync_changes_nothing(self):
        reference_data.sync_permissions()
        result = reference_data.sync_permissions()
        self.assertEqual((result.created, result.updated), ([], []))
        self.assertEqual(len(result.unchanged), 3)
        self.assertEqual(Permission.objects.count(), 3)

    def test_having_roles_and_permissions_still_creates_no_assignments(self):
        reference_data.sync_roles()
        reference_data.sync_permissions()
        reference_data.sync_permissions()
        self.assertEqual(RolePermission.objects.count(), 0)

    def test_a_changed_description_updates_the_row_and_keeps_its_assignments(self):
        reference_data.sync_roles()
        reference_data.sync_permissions()
        role = Role.objects.get(role_name="Office Staff")
        RolePermission.objects.create(role=role, permission=Permission.objects.get(permission_key="client.view"))
        changed = (reference_data.PermissionDefinition("client.view", "clients", "A new description"),)
        with mock.patch.object(reference_data, "PERMISSION_DEFINITIONS", changed):
            result = reference_data.sync_permissions()
        self.assertEqual(result.updated, ["client.view"])
        self.assertEqual(Permission.objects.get(permission_key="client.view").description, "A new description")
        self.assertEqual(RolePermission.objects.count(), 1)

    def test_a_permission_not_in_the_registry_is_reported_and_not_deleted(self):
        Permission.objects.create(permission_key="old.key", module="old")
        result = reference_data.sync_permissions()
        self.assertEqual(result.orphans, ["old.key"])
        self.assertTrue(Permission.objects.filter(permission_key="old.key").exists())


class RegistryValidationTests(TestCase):
    def assertRejected(self, definitions, message_part):
        with mock.patch.object(reference_data, "PERMISSION_DEFINITIONS", definitions):
            with self.assertRaises(reference_data.RegistryError) as ctx:
                reference_data.sync_permissions()
        self.assertIn(message_part, str(ctx.exception))
        self.assertEqual(Permission.objects.count(), 0)  # nothing was written

    def test_a_blank_key_or_module_is_rejected(self):
        D = reference_data.PermissionDefinition
        self.assertRejected((D("client.view", "clients"), D("  ", "clients")), "blank")
        self.assertRejected((D("client.view", ""),), "blank")

    def test_too_long_values_are_rejected_using_the_model_limits(self):
        D = reference_data.PermissionDefinition
        key_limit = Permission._meta.get_field("permission_key").max_length
        module_limit = Permission._meta.get_field("module").max_length
        self.assertRejected((D("k" * (key_limit + 1), "clients"),), "too long")
        self.assertRejected((D("client.view", "m" * (module_limit + 1)),), "too long")

    def test_duplicate_keys_are_rejected(self):
        D = reference_data.PermissionDefinition
        self.assertRejected((D("client.view", "clients"), D("client.view", "clients")), "more than once")
