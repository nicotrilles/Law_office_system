"""Usage: python manage.py seed_reference_data

Creates the two roles (Office Staff, Attorney) if they are missing. Creates no permissions and no
role-permission assignments. Safe to run any number of times.
"""
import logging

from django.core.management.base import BaseCommand, CommandError
from django.db.utils import OperationalError, ProgrammingError

from apps.accounts import reference_data

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Create the Office Staff and Attorney roles if missing. Creates no permissions or assignments."

    def handle(self, *args, **options):
        try:
            result = reference_data.sync_roles()
        except reference_data.RoleNameConflict as exc:
            raise CommandError(str(exc))
        except (ProgrammingError, OperationalError):
            logger.exception("seed_reference_data failed")
            raise CommandError(
                "Could not read or write the roles table. Check that PostgreSQL is running and "
                "run 'python manage.py migrate' first. Details were written to the log."
            )

        self.stdout.write(f"Roles: {len(result.created)} created, {len(result.unchanged)} unchanged.")
        self.stdout.write("Permissions and role-permission assignments: untouched (none are seeded).")
