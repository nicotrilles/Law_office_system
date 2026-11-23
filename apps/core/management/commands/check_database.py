"""Usage: python manage.py check_database  -- confirms the database connection works."""
import logging

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import Error as DatabaseError
from django.db import connection
from django.db.migrations.executor import MigrationExecutor

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Verify the database connection and print non-sensitive details (never the password)."

    def handle(self, *args, **options):
        db = settings.DATABASES["default"]
        try:
            connection.ensure_connection()
            with connection.cursor() as cursor:
                cursor.execute("SHOW server_version")
                version = cursor.fetchone()[0]
            executor = MigrationExecutor(connection)
            pending = executor.migration_plan(executor.loader.graph.leaf_nodes())
            throttle_table = settings.CACHES["login_throttle"]["LOCATION"]
            throttle_table_present = throttle_table in connection.introspection.table_names()
        except DatabaseError as exc:
            logger.exception("check_database failed")
            raise CommandError(
                f"Could not connect to the database ({exc.__class__.__name__}). "
                "Check DATABASE_URL in your .env file and that PostgreSQL is running. "
                "Full details were written to the log."
            )

        self.stdout.write(self.style.SUCCESS("Connection OK"))
        self.stdout.write(f"  Database : {db['NAME']}")
        self.stdout.write(f"  Host     : {db['HOST'] or 'local socket'}:{db['PORT'] or 'default'}")
        self.stdout.write(f"  User     : {db['USER']}")
        self.stdout.write(f"  PostgreSQL version: {version}")
        self.stdout.write(f"  Unapplied migrations: {len(pending)}")
        if throttle_table_present:
            self.stdout.write(f"  Sign-in throttle table ({throttle_table}): present")
        else:
            self.stdout.write(self.style.WARNING(
                f"  Sign-in throttle table ({throttle_table}): MISSING. "
                "Sign-in is refused until you run: python manage.py createcachetable"
            ))
