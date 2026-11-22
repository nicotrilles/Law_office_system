"""Tests for the PERMISSIONS and ROLE_PERMISSIONS tables (checkpoint 4.1.2 and 4.1.3)."""
import ast
from pathlib import Path

from django.apps import apps
from django.conf import settings
from django.db import IntegrityError, connection, transaction
from django.db.migrations.loader import MigrationLoader
from django.db.migrations.operations import CreateModel
from django.db.models.deletion import ProtectedError
from django.test import TestCase, TransactionTestCase

from apps.accounts.models import Permission, Role, RolePermission, User


def table_columns(table):
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT column_name, data_type, character_maximum_length, is_nullable "
            "FROM information_schema.columns WHERE table_name = %s", [table]
        )
        return {name: (dtype, length, nullable) for name, dtype, length, nullable in cursor.fetchall()}


class SchemaTests(TestCase):
    def test_permissions_table_columns(self):
        cols = table_columns("permissions")
        self.assertEqual(set(cols), {"permission_id", "permission_key", "module", "description"})
        self.assertEqual(cols["permission_id"][0], "bigint")
        self.assertEqual(cols["permission_key"][:2], ("character varying", 100))
        self.assertEqual(cols["module"][:2], ("character varying", 50))
        self.assertEqual(cols["description"][:2], ("character varying", 255))
        nullable = {name for name, (_, _, is_null) in cols.items() if is_null == "YES"}
        self.assertEqual(nullable, {"description"})

    def test_role_permissions_table_columns(self):
        cols = table_columns("role_permissions")
        self.assertEqual(set(cols), {"role_id", "permission_id"})  # no surrogate id column
        for name in cols:
            self.assertEqual(cols[name][0], "bigint")
            self.assertEqual(cols[name][2], "NO")

    def test_role_permissions_primary_key_is_the_pair_in_order(self):
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT kcu.column_name FROM information_schema.table_constraints tc "
                "JOIN information_schema.key_column_usage kcu "
                "ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema "
                "WHERE tc.table_name = %s AND tc.constraint_type = 'PRIMARY KEY' "
                "ORDER BY kcu.ordinal_position", ["role_permissions"]
            )
            self.assertEqual([row[0] for row in cursor.fetchall()], ["role_id", "permission_id"])

    def test_new_models_do_not_ask_django_to_create_its_own_permissions(self):
        self.assertEqual(Permission._meta.default_permissions, ())
        self.assertEqual(RolePermission._meta.default_permissions, ())

    def test_migration_0002_only_creates_the_two_tables(self):
        loader = MigrationLoader(connection, load=False)
        loader.load_disk()
        keys = [k for k in loader.disk_migrations if k[0] == "accounts" and k[1].startswith("0002")]
        self.assertEqual(len(keys), 1)
        migration = loader.disk_migrations[keys[0]]
        self.assertIn(("accounts", "0001_initial"), migration.dependencies)
        # No RunPython/RunSQL: the migration can never insert data.
        self.assertTrue(all(isinstance(op, CreateModel) for op in migration.operations))
        self.assertEqual({op.name for op in migration.operations}, {"Permission", "RolePermission"})


class ConstraintTests(TestCase):
    def setUp(self):
        self.role = Role.objects.create(role_name="Office Staff")
        self.other_role = Role.objects.create(role_name="Attorney")
        self.read = Permission.objects.create(permission_key="demo.read", module="demo")
        self.write = Permission.objects.create(permission_key="demo.write", module="demo")

    def test_permission_key_is_unique(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Permission.objects.create(permission_key="demo.read", module="demo")

    def test_the_same_role_and_permission_cannot_be_linked_twice(self):
        RolePermission.objects.create(role=self.role, permission=self.read)
        with self.assertRaises(IntegrityError), transaction.atomic():
            RolePermission.objects.create(role=self.role, permission=self.read)

    def test_many_to_many_works(self):
        for role in (self.role, self.other_role):
            for permission in (self.read, self.write):
                RolePermission.objects.create(role=role, permission=permission)
        self.assertEqual(RolePermission.objects.filter(role=self.role).count(), 2)
        self.assertEqual(RolePermission.objects.filter(permission=self.read).count(), 2)

    def test_deleting_a_role_with_assignments_is_refused(self):
        RolePermission.objects.create(role=self.role, permission=self.read)
        with self.assertRaises(ProtectedError):
            self.role.delete()

    def test_deleting_an_assigned_permission_is_refused(self):
        RolePermission.objects.create(role=self.role, permission=self.read)
        with self.assertRaises(ProtectedError):
            self.read.delete()

    def test_a_valid_link_passes_the_forced_foreign_key_check(self):
        RolePermission.objects.create(role=self.role, permission=self.read)
        connection.check_constraints()  # must not raise


class DeferredForeignKeyInsideTestCase(TestCase):
    """PostgreSQL checks these foreign keys at COMMIT, not at INSERT (they are DEFERRABLE INITIALLY
    DEFERRED). Django's TestCase never commits, so the check is forced with check_constraints()."""

    def test_invalid_link_is_detected_when_the_deferred_check_is_forced(self):
        raised_at_create = False
        with self.assertRaises(IntegrityError):
            with transaction.atomic():  # a savepoint, rolled back when the error leaves the block
                try:
                    RolePermission.objects.create(role_id=999999, permission_id=999999)
                except IntegrityError:
                    raised_at_create = True
                    raise
                connection.check_constraints()
        self.assertFalse(raised_at_create, "create() must not raise: the constraint is deferred")
        self.assertEqual(RolePermission.objects.count(), 0)


class DeferredForeignKeyAtRealCommit(TransactionTestCase):
    """TransactionTestCase really commits, so this tests the actual PostgreSQL behaviour."""

    def test_invalid_link_raises_at_commit_not_at_create(self):
        create_returned = False
        with self.assertRaises(IntegrityError):
            with transaction.atomic():  # the outermost block: leaving it issues COMMIT
                RolePermission.objects.create(role_id=999999, permission_id=999999)
                create_returned = True
        self.assertTrue(create_returned, "create() returned normally; the error came at commit")
        self.assertEqual(RolePermission.objects.count(), 0)


class DjangoAuthSeparationTests(TestCase):
    """Django's built-in Groups and Permissions must never become the authorization authority."""

    def test_new_models_have_no_relation_to_django_permission_or_group(self):
        django_models = {apps.get_model("auth", "Permission"), apps.get_model("auth", "Group")}
        for model in (Permission, RolePermission):
            related = {f.related_model for f in model._meta.get_fields() if f.is_relation}
            self.assertFalse(related & django_models, model.__name__)

    def test_user_has_no_django_permission_machinery(self):
        for name in ("has_perm", "has_perms", "groups", "user_permissions"):
            self.assertFalse(hasattr(User, name), name)

    def test_project_code_does_not_import_django_permission_or_group(self):
        # An import scan. It does not catch lookups by name such as apps.get_model("auth", "Permission").
        offenders = []
        for path in (Path(settings.BASE_DIR) / "apps").rglob("*.py"):
            if {"tests", "migrations"} & set(path.parts):
                continue
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                if isinstance(node, ast.ImportFrom) and node.module == "django.contrib.auth.models":
                    if any(alias.name in ("Permission", "Group") for alias in node.names):
                        offenders.append(str(path))
        self.assertEqual(offenders, [])
