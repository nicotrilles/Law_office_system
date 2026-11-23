"""Usage: python manage.py create_user

Creates an OFFICE STAFF account. This command has no --role option and cannot create an Attorney
(use setup_attorney for the one Attorney). The password is typed at a hidden prompt. Assigns no
permissions.
"""
import logging

from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError
from django.db.utils import OperationalError, ProgrammingError

from apps.accounts import reference_data
from apps.accounts.management import prompts
from apps.accounts.models import Role, User

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Create an Office Staff account (password typed at a hidden prompt). Cannot create an Attorney."

    def add_arguments(self, parser):
        parser.add_argument("--username", help="Asked for if omitted.")
        parser.add_argument("--full-name", dest="full_name", help="Asked for if omitted.")

    def handle(self, *args, **options):
        prompts.require_interactive()
        try:
            reference_data.sync_roles()
            role = Role.objects.get(role_name=reference_data.OFFICE_STAFF_ROLE)
        except reference_data.RoleNameConflict as exc:
            raise CommandError(str(exc))
        except (ProgrammingError, OperationalError):
            logger.exception("create_user could not reach the roles table")
            raise CommandError(prompts.MIGRATE_HINT)

        username = prompts.clean_username(options["username"] or input("Username: "))
        full_name = prompts.clean_full_name(options["full_name"] or input("Full name: "))
        if User.objects.filter(username__iexact=username).exists():
            raise CommandError("That username is already in use.")
        password = prompts.read_new_password(username, full_name, self.stderr.write)

        try:
            User.objects.create_user(username, full_name, role, password)
        except IntegrityError:
            raise CommandError("That username is already in use.")

        logger.info("Office Staff account created: %s", username)
        self.stdout.write(self.style.SUCCESS(f'Created Office Staff account "{username}".'))
        self.stdout.write("No permissions have been assigned.")
