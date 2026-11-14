from django.contrib.auth import authenticate, get_user_model
from django.db import IntegrityError, connection, transaction
from django.db.models.deletion import ProtectedError
from django.test import TestCase

from apps.accounts.models import Role

User = get_user_model()
PASSWORD = "correct-horse-battery-staple"


def columns(table):
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT column_name, data_type, character_maximum_length, is_nullable "
            "FROM information_schema.columns WHERE table_name = %s", [table]
        )
        return {name: (dtype, length, nullable) for name, dtype, length, nullable in cursor.fetchall()}


class SchemaMappingTests(TestCase):
    """The tables must match the logical schema checkpoint v1.2, section 4.1."""

    def test_users_table_columns(self):
        cols = columns("users")
        self.assertEqual(
            set(cols),
            {"user_id", "role_id", "full_name", "username", "password_hash",
             "account_status", "created_at", "updated_at"},
        )
        self.assertNotIn("last_login", cols)  # not in the schema
        self.assertEqual(cols["user_id"][0], "bigint")
        self.assertEqual(cols["password_hash"][1], 255)
        self.assertEqual(cols["full_name"][1], 150)
        self.assertEqual(cols["username"][1], 50)
        self.assertEqual(cols["account_status"][1], 20)
        self.assertTrue(all(nullable == "NO" for *_, nullable in cols.values()))

    def test_roles_table_columns(self):
        cols = columns("roles")
        self.assertEqual(set(cols), {"role_id", "role_name", "description"})
        self.assertEqual(cols["role_name"][1], 50)
        self.assertEqual(cols["description"][2], "YES")  # nullable in the schema


class UserCreationTests(TestCase):
    def setUp(self):
        self.role = Role.objects.create(role_name="Office Staff")

    def test_password_is_stored_as_an_argon2_hash_never_plaintext(self):
        user = User.objects.create_user("maria", "Maria Santos", self.role, PASSWORD)
        stored = User.objects.get(pk=user.pk).password
        self.assertTrue(stored.startswith("argon2$"))
        self.assertNotIn(PASSWORD, stored)
        self.assertTrue(user.check_password(PASSWORD))
        self.assertFalse(user.check_password("wrong"))

    def test_create_user_requires_username_full_name_role_and_password(self):
        with self.assertRaises(ValueError):
            User.objects.create_user("", "Name", self.role, PASSWORD)
        with self.assertRaises(ValueError):
            User.objects.create_user("a", "", self.role, PASSWORD)
        with self.assertRaises(ValueError):
            User.objects.create_user("a", "Name", None, PASSWORD)
        with self.assertRaises(ValueError):
            User.objects.create_user("a", "Name", self.role, "")

    def test_createsuperuser_is_not_supported(self):
        with self.assertRaises(NotImplementedError):
            User.objects.create_superuser("x")

    def test_username_is_unique_ignoring_case(self):
        User.objects.create_user("Maria", "Maria Santos", self.role, PASSWORD)
        with self.assertRaises(IntegrityError), transaction.atomic():
            User.objects.create_user("maria", "Someone Else", self.role, PASSWORD)

    def test_database_rejects_an_invalid_account_status(self):
        user = User.objects.create_user("maria", "Maria Santos", self.role, PASSWORD)
        with self.assertRaises(IntegrityError), transaction.atomic():
            User.objects.filter(pk=user.pk).update(account_status="banned")

    def test_a_role_with_users_cannot_be_deleted(self):
        User.objects.create_user("maria", "Maria Santos", self.role, PASSWORD)
        with self.assertRaises(ProtectedError):
            self.role.delete()

    def test_role_names_are_unique(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Role.objects.create(role_name="Office Staff")

    def test_user_requires_a_role_at_the_database_level(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            User.objects.bulk_create([User(username="x", full_name="X", password="h", role_id=None)])


class AccountStatusAndLoginTests(TestCase):
    def setUp(self):
        self.role = Role.objects.create(role_name="Office Staff")
        self.user = User.objects.create_user("maria", "Maria Santos", self.role, PASSWORD)

    def test_is_active_follows_account_status(self):
        self.assertTrue(self.user.is_active)
        self.user.account_status = User.AccountStatus.INACTIVE
        self.assertFalse(self.user.is_active)

    def test_authentication_is_case_insensitive_on_username(self):
        self.assertEqual(authenticate(username="MARIA", password=PASSWORD), self.user)

    def test_wrong_password_is_rejected(self):
        self.assertIsNone(authenticate(username="maria", password="nope"))

    def test_deactivated_account_cannot_authenticate(self):
        User.objects.filter(pk=self.user.pk).update(account_status="inactive")
        self.assertIsNone(authenticate(username="maria", password=PASSWORD))

    def test_session_login_works_without_a_last_login_column(self):
        # Guards the 'last_login = None' decision: Django must not try to update that column.
        self.assertTrue(self.client.login(username="maria", password=PASSWORD))
        self.assertIn("_auth_user_id", self.client.session)

    def test_password_hash_is_not_part_of_the_string_forms(self):
        self.assertNotIn(self.user.password, str(self.user))
        self.assertNotIn(self.user.password, repr(self.user))
