"""Shared input helpers for the account commands. No database access here.

There is deliberately NO way to give a password on the command line (it would end up in the shell
history). Passwords are only ever typed at a hidden prompt.
"""
import getpass
import sys

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import CommandError

from apps.accounts.models import User

MAX_PASSWORD_ATTEMPTS = 3
MIGRATE_HINT = (
    "Could not read or write the roles table. Check that PostgreSQL is running and run "
    "'python manage.py migrate' first."
)


def _stdin_is_interactive():
    return sys.stdin.isatty()


def require_interactive():
    if not _stdin_is_interactive():
        raise CommandError(
            "This command asks for a password at a hidden prompt, so it must be run in an "
            "interactive terminal."
        )


def _clean(raw, field, label):
    value = (raw or "").strip()
    if not value:
        raise CommandError(f"The {label} cannot be empty.")
    limit = User._meta.get_field(field).max_length  # read from the model, never typed here
    if len(value) > limit:
        raise CommandError(f"The {label} is too long ({len(value)} characters). The limit is {limit}.")
    return value


def clean_username(raw):
    return _clean(raw, "username", "username")


def clean_full_name(raw):
    return _clean(raw, "full_name", "full name")


def read_new_password(username, full_name, write):
    """Ask twice at a hidden prompt, validate with Django's validators, allow three tries."""
    candidate = User(username=username, full_name=full_name)  # lets the similarity validator compare
    for _ in range(MAX_PASSWORD_ATTEMPTS):
        password = getpass.getpass("Password: ")
        confirmation = getpass.getpass("Password (again): ")
        if password != confirmation:
            write("The two passwords do not match. Try again.")
            continue
        try:
            validate_password(password, user=candidate)
        except ValidationError as exc:
            for message in exc.messages:
                write(message)
            continue
        return password
    raise CommandError("No valid password was entered. Nothing was created.")
