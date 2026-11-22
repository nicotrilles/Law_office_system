"""
Reference data that must exist in the database.

Plain Python only: importing this module never touches the database. Models are imported inside
the function that needs them.
"""
from collections import namedtuple

from django.db import transaction

OFFICE_STAFF_ROLE = "Office Staff"
ATTORNEY_ROLE = "Attorney"
ROLE_NAMES = (OFFICE_STAFF_ROLE, ATTORNEY_ROLE)

# Intentionally empty (decision Q5). A permission key is added here only by the milestone whose
# features need it, after the keys are approved. Role-to-permission assignments are never seeded.
PERMISSION_DEFINITIONS = ()

SeedResult = namedtuple("SeedResult", ["created", "unchanged"])


class RoleNameConflict(Exception):
    """A role exists whose name differs from a required name only in capital letters."""


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
