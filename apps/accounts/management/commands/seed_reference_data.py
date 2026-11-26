"""Usage: python manage.py seed_reference_data

Creates the two roles (Office Staff, Attorney) and the permission DEFINITIONS if they are missing.
Creates NO role-to-permission assignment (use `manage.py role_permissions grant`). Safe to run any
number of times.
"""
import logging

from django.core.management.base import BaseCommand, CommandError
from django.db.utils import OperationalError, ProgrammingError

from apps.accounts import reference_data

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Create the two roles and the permission definitions if missing. Creates no assignments."

    def handle(self, *args, **options):
        try:
            roles = reference_data.sync_roles()
            permissions = reference_data.sync_permissions()
        except (reference_data.RoleNameConflict, reference_data.RegistryError) as exc:
            raise CommandError(str(exc))
        except (ProgrammingError, OperationalError):
            logger.exception("seed_reference_data failed")
            raise CommandError(
                "Could not read or write the roles or permissions tables. Check that PostgreSQL is "
                "running and run 'python manage.py migrate' first. Details were written to the log."
            )

        self.stdout.write(f"Roles: {len(roles.created)} created, {len(roles.unchanged)} unchanged.")
        self.stdout.write(
            f"Permissions: {len(permissions.created)} created, {len(permissions.updated)} updated, "
            f"{len(permissions.unchanged)} unchanged."
        )
        if permissions.orphans:
            self.stdout.write(self.style.WARNING(
                "WARNING: permissions in the database that are not in the registry (left untouched): "
                + ", ".join(permissions.orphans)
            ))
        self.stdout.write("Role-permission assignments: untouched. Use 'python manage.py role_permissions'.")
