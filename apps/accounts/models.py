"""
Access-control models (logical schema checkpoint v1.3, section 4.1).

Milestone 1 only defines ROLES and USERS, because the custom user model must exist
before the first migration. PERMISSIONS and ROLE_PERMISSIONS arrive in Milestone 2.

Django's built-in Permission and Group tables are NOT used. Application code will check
permission keys through the user's role (PD-F), never role names and never per-user overrides.
"""
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.db import models
from django.db.models.functions import Lower


class Role(models.Model):
    """ROLES: seeded with 'Office Staff' and 'Attorney' in Milestone 2."""

    role_id = models.BigAutoField(primary_key=True)
    role_name = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = "roles"
        default_permissions = ()

    def __str__(self):
        return self.role_name


class UserManager(BaseUserManager):
    use_in_migrations = True

    def get_by_natural_key(self, username):
        # Usernames are compared case-insensitively (schema note on USERS.username).
        return self.get(username__iexact=username)

    def create_user(self, username, full_name, role, password):
        if not username or not username.strip():
            raise ValueError("A username is required.")
        if not full_name or not full_name.strip():
            raise ValueError("A full name is required.")
        if role is None:
            raise ValueError("Every user must have a role.")
        if not password:
            raise ValueError("A password is required.")
        user = self.model(username=username.strip(), full_name=full_name.strip(), role=role)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, *args, **kwargs):
        raise NotImplementedError(
            "This project has no superuser concept. The initial Attorney account is created "
            "by the one-time setup command (Milestone 2)."
        )


class User(AbstractBaseUser):
    """USERS table. One role per user (PD-F). Accounts are deactivated, never deleted."""

    class AccountStatus(models.TextChoices):
        ACTIVE = "active", "Active"
        INACTIVE = "inactive", "Inactive"

    user_id = models.BigAutoField(primary_key=True)
    # ON DELETE RESTRICT in the schema. Django's PROTECT blocks deletion in the application
    # and the database foreign key (NO ACTION) blocks it at commit time.
    role = models.ForeignKey(
        Role, on_delete=models.PROTECT, db_column="role_id", related_name="users"
    )
    full_name = models.CharField(max_length=150)
    username = models.CharField(max_length=50, unique=True)
    # Schema column is password_hash VARCHAR(255). Holds an Argon2 hash, never plaintext.
    password = models.CharField("password hash", max_length=255, db_column="password_hash")
    account_status = models.CharField(
        max_length=20, choices=AccountStatus.choices, default=AccountStatus.ACTIVE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # The schema has no last_login column. Setting this to None removes the field Django
    # would otherwise add. Login events will be recorded in an activity log in a later
    # milestone (the activity log is deferred).
    last_login = None

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        db_table = "users"
        default_permissions = ()
        constraints = [
            models.CheckConstraint(
                condition=models.Q(account_status__in=["active", "inactive"]),
                name="ck_users_account_status",
            ),
            # Case-insensitive uniqueness: "Maria" and "maria" are the same username.
            models.UniqueConstraint(Lower("username"), name="uq_users_username_ci"),
        ]

    @property
    def is_active(self):
        """Django uses this to refuse login for deactivated accounts."""
        return self.account_status == self.AccountStatus.ACTIVE

    def get_full_name(self):
        return self.full_name

    def __str__(self):
        return self.username


class Permission(models.Model):
    """PERMISSIONS table (checkpoint 4.1.2). This is NOT Django's built-in Permission model.

    Authorization uses only this table and ROLE_PERMISSIONS, reached through the user's role.
    No rows are seeded and none are assigned in Milestone 2.
    """

    permission_id = models.BigAutoField(primary_key=True)
    permission_key = models.CharField(max_length=100, unique=True)
    module = models.CharField(max_length=50)
    description = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = "permissions"
        default_permissions = ()

    def __str__(self):
        return self.permission_key


class RolePermission(models.Model):
    """ROLE_PERMISSIONS table (checkpoint 4.1.3): a row means the role holds the permission.

    The primary key is the pair (role_id, permission_id), so a row's ``pk`` is a tuple.
    To refuse a duplicate pair use ``objects.create()``. Calling ``save()`` on a pair that already
    exists silently does nothing.
    """

    pk = models.CompositePrimaryKey("role_id", "permission_id")
    role = models.ForeignKey(
        Role, on_delete=models.PROTECT, db_column="role_id", related_name="role_permissions"
    )
    permission = models.ForeignKey(
        Permission, on_delete=models.PROTECT, db_column="permission_id", related_name="role_permissions"
    )

    class Meta:
        db_table = "role_permissions"
        default_permissions = ()
