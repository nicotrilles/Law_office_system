"""Usage: python manage.py setup_attorney

Creates the one initial Attorney account. Refuses if ANY Attorney account already exists, active or
inactive. The password is typed at a hidden prompt, validated, and stored only as an Argon2 hash.
Assigns no permissions and creates no Django superuser.
"""
import logging

from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError, transaction
from django.db.utils import OperationalError, ProgrammingError

from apps.accounts import reference_data
from apps.accounts.management import prompts
from apps.accounts.models import Role, User

logger = logging.getLogger(__name__)

ALREADY_EXISTS = (
    "An Attorney account already exists (active or inactive), so no new one was created. "
    "Only one Attorney account is allowed."
)


class Command(BaseCommand):
    help = "Create the one initial Attorney account (password typed at a hidden prompt)."

    def add_arguments(self, parser):
        parser.add_argument("--username", help="Asked for if omitted.")
        parser.add_argument("--full-name", dest="full_name", help="Asked for if omitted.")

    def handle(self, *args, **options):
        prompts.require_interactive()
        try:
            reference_data.sync_roles()  # makes sure the two roles exist (safe to repeat)
        except reference_data.RoleNameConflict as exc:
            raise CommandError(str(exc))
        except (ProgrammingError, OperationalError):
            logger.exception("setup_attorney could not reach the roles table")
            raise CommandError(prompts.MIGRATE_HINT)

        # Refuse early, before asking for anything.
        if User.objects.filter(role__role_name=reference_data.ATTORNEY_ROLE).exists():
            raise CommandError(ALREADY_EXISTS)

        username = prompts.clean_username(options["username"] or input("Username: "))
        full_name = prompts.clean_full_name(options["full_name"] or input("Full name: "))
        if User.objects.filter(username__iexact=username).exists():
            raise CommandError("That username is already in use.")
        password = prompts.read_new_password(username, full_name, self.stderr.write)

        try:
            with transaction.atomic():
                # Lock the Attorney role row. A second run waits here, then sees the first run's
                # account, so two simultaneous runs cannot both succeed.
                role = Role.objects.select_for_update().get(role_name=reference_data.ATTORNEY_ROLE)
                if User.objects.filter(role=role).exists():
                    raise CommandError(ALREADY_EXISTS)
                User.objects.create_user(username, full_name, role, password)
        except IntegrityError:
            raise CommandError("That username is already in use.")

        logger.info("Initial Attorney account created: %s", username)
        self.stdout.write(self.style.SUCCESS(f'Created Attorney account "{username}".'))
        self.stdout.write("No permissions have been assigned.")
