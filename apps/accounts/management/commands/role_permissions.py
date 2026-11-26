"""Usage:
    python manage.py role_permissions list
    python manage.py role_permissions grant  --role "Office Staff" --permission client.view
    python manage.py role_permissions revoke --role "Office Staff" --permission client.view

The only supported way to assign permissions to roles. It applies exactly what it is told and never
assigns anything on its own. Both grant and revoke are safe to repeat.
"""
import logging

from django.core.management.base import BaseCommand, CommandError
from django.db.utils import OperationalError, ProgrammingError

from apps.accounts import reference_data
from apps.accounts.models import Permission, Role, RolePermission

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "List, grant, or revoke the permissions held by a role."

    def add_arguments(self, parser):
        actions = parser.add_subparsers(dest="action", required=True)
        actions.add_parser("list", help="Show which role holds which permission (read-only).")
        for name, text in (("grant", "Give a role a permission."), ("revoke", "Take a permission from a role.")):
            sub = actions.add_parser(name, help=text)
            sub.add_argument("--role", required=True, help='For example "Office Staff".')
            sub.add_argument("--permission", required=True, help="For example client.view.")

    def handle(self, *args, **options):
        try:
            if options["action"] == "list":
                self.list_matrix()
            else:
                self.change(options["action"], options["role"], options["permission"])
        except (ProgrammingError, OperationalError):
            logger.exception("role_permissions could not reach the database")
            raise CommandError("Could not read or write the permission tables. Check that PostgreSQL is "
                               "running and run 'python manage.py migrate' first. Details are in the log.")

    # ---- list ----
    def list_matrix(self):
        roles = list(Role.objects.order_by("role_name"))
        if not roles:
            raise CommandError("No roles exist yet. Run 'python manage.py seed_reference_data' first.")
        seeded = {p.permission_key: p for p in Permission.objects.all()}
        granted = set(RolePermission.objects.values_list("role_id", "permission_id"))
        defined = [d.key for d in reference_data.PERMISSION_DEFINITIONS]
        rows = [(key, seeded.get(key), "" if key in seeded else "NOT SEEDED (run seed_reference_data)") for key in defined]
        rows += [(key, perm, "not in the registry") for key, perm in sorted(seeded.items()) if key not in defined]

        width = max([len("Permission")] + [len(key) for key, _, _ in rows])
        header = "Permission".ljust(width) + "  " + "  ".join(r.role_name.ljust(max(len(r.role_name), 3)) for r in roles)
        self.stdout.write(header)
        for key, perm, note in rows:
            cells = []
            for role in roles:
                mark = "yes" if perm is not None and (role.pk, perm.pk) in granted else "-"
                cells.append(mark.ljust(max(len(role.role_name), 3)))
            self.stdout.write(key.ljust(width) + "  " + "  ".join(cells) + (f"  <- {note}" if note else ""))

    # ---- grant / revoke ----
    def change(self, action, role_name, key):
        try:
            role = Role.objects.get(role_name=role_name)
        except Role.DoesNotExist:
            names = ", ".join(Role.objects.order_by("role_name").values_list("role_name", flat=True)) or "(none)"
            raise CommandError(f"No role named {role_name!r}. Available roles: {names}.")

        if action == "grant":
            if key not in {d.key for d in reference_data.PERMISSION_DEFINITIONS}:
                defined = ", ".join(d.key for d in reference_data.PERMISSION_DEFINITIONS)
                raise CommandError(f"{key!r} is not a defined permission. Defined permissions: {defined}.")
            permission = Permission.objects.filter(permission_key=key).first()
            if permission is None:
                raise CommandError(f"{key!r} is defined but not in the database yet. "
                                   "Run 'python manage.py seed_reference_data' first.")
            _, created = RolePermission.objects.get_or_create(role=role, permission=permission)
            if created:
                logger.info("Permission granted: role=%s permission=%s", role.role_name, key)
                self.stdout.write(self.style.SUCCESS(f"Granted {key} to {role.role_name}."))
            else:
                self.stdout.write(f"{role.role_name} already holds {key}. No change.")
        else:  # revoke. Works for any permission that exists, even one removed from the registry.
            permission = Permission.objects.filter(permission_key=key).first()
            if permission is None:
                raise CommandError(f"No permission with the key {key!r} exists.")
            deleted, _ = RolePermission.objects.filter(role=role, permission=permission).delete()
            if deleted:
                logger.info("Permission revoked: role=%s permission=%s", role.role_name, key)
                self.stdout.write(self.style.SUCCESS(f"Revoked {key} from {role.role_name}."))
            else:
                self.stdout.write(f"{role.role_name} did not hold {key}. No change.")
