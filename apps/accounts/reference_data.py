"""
Reference data that must exist in the database.

Plain Python only: importing this module never touches the database. Models are imported inside
the functions that need them.

Three things are deliberately kept separate:
- ROLE_NAMES: the roles that must exist.
- PERMISSION_DEFINITIONS: the permissions that EXIST (the registry). Defining a permission gives it
  to nobody.
- Role-to-permission ASSIGNMENTS are not here at all. They are made explicitly, one at a time, with
  `python manage.py role_permissions grant ...`.
"""
from collections import namedtuple
from typing import NamedTuple

from django.db import transaction

OFFICE_STAFF_ROLE = "Office Staff"
ATTORNEY_ROLE = "Attorney"
ROLE_NAMES = (OFFICE_STAFF_ROLE, ATTORNEY_ROLE)


class PermissionDefinition(NamedTuple):
    key: str
    module: str
    description: str = ""


# The approved permissions. A key is added here only after it has been approved. Service Request
# permissions (request.*) are NOT defined yet.
PERMISSION_DEFINITIONS = (
    PermissionDefinition("client.view", "clients", "View and search client records"),
    PermissionDefinition("client.create", "clients", "Create new client records"),
    PermissionDefinition("client.edit", "clients", "Edit existing client records"),
)

SeedResult = namedtuple("SeedResult", ["created", "unchanged"])
PermissionSyncResult = namedtuple("PermissionSyncResult", ["created", "updated", "unchanged", "orphans"])


class RoleNameConflict(Exception):
    """A role exists whose name differs from a required name only in capital letters."""


class RegistryError(Exception):
    """A permission definition is invalid (blank, too long, or duplicated)."""


def sync_roles():
    """Create any missing required role. Never edits or deletes a role. Safe to run repeatedly."""
    from .models import Role

    created, unchanged = [], []
    with transaction.atomic():
        existing = set(Role.objects.values_list("role_name", flat=True))
        for name in ROLE_NAMES:
            clashes = sorted(n for n in existing if n.lower() == name.lower() and n != name)
            if clashes:
                raise RoleNameConflict(
                    f"A role named {clashes[0]!r} already exists. It differs from {name!r} only in "
                    "capital letters. Rename or remove it, then run this command again."
                )
        for name in ROLE_NAMES:
            _, was_created = Role.objects.get_or_create(role_name=name)
            (created if was_created else unchanged).append(name)
    return SeedResult(created, unchanged)


def validate_registry():
    """Reject a bad registry BEFORE anything is written. Limits are read from the model."""
    from .models import Permission

    limits = {
        "key": Permission._meta.get_field("permission_key").max_length,
        "module": Permission._meta.get_field("module").max_length,
        "description": Permission._meta.get_field("description").max_length,
    }
    seen = set()
    for definition in PERMISSION_DEFINITIONS:
        for part in ("key", "module"):
            value = getattr(definition, part)
            if not value or value != value.strip():
                raise RegistryError(f"Permission definition {definition!r}: the {part} is blank or has "
                                    "leading or trailing spaces.")
        for part, limit in limits.items():
            length = len(getattr(definition, part) or "")
            if length > limit:
                raise RegistryError(f"Permission {definition.key!r}: the {part} is too long "
                                    f"({length} characters). The limit is {limit}.")
        if definition.key in seen:
            raise RegistryError(f"The permission key {definition.key!r} is defined more than once.")
        seen.add(definition.key)


def sync_permissions():
    """Make the `permissions` table match the registry. Creates or updates definition rows.

    NEVER creates a role-to-permission assignment, and never deletes anything: a row that is not in
    the registry is only reported (an "orphan").
    """
    from .models import Permission

    validate_registry()
    created, updated, unchanged = [], [], []
    with transaction.atomic():
        for definition in PERMISSION_DEFINITIONS:
            description = definition.description or None
            row, was_created = Permission.objects.get_or_create(
                permission_key=definition.key,
                defaults={"module": definition.module, "description": description},
            )
            if was_created:
                created.append(definition.key)
            elif row.module != definition.module or row.description != description:
                row.module, row.description = definition.module, description
                row.save(update_fields=["module", "description"])
                updated.append(definition.key)
            else:
                unchanged.append(definition.key)
        defined = {d.key for d in PERMISSION_DEFINITIONS}
        orphans = sorted(set(Permission.objects.values_list("permission_key", flat=True)) - defined)
    return PermissionSyncResult(created, updated, unchanged, orphans)
