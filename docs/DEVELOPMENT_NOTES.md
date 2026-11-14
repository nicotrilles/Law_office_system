# Development Notes

Everything here is **provisional** unless explicitly marked confirmed. Nothing in this file is
confirmed office policy.

## 1. Approved decisions (project team review)

| ID | Decision |
|---|---|
| D1 | Django 5.2 LTS, PostgreSQL, server-rendered pages. |
| D2 | Build incrementally. Create each module's tables when that module is built. The schema checkpoint (v1.2) stays the provisional reference. |
| D3 | The initial Attorney account is created by a one-time command-line command with a securely prompted password. No default credentials. |
| D4 | Seed the two roles and the permission definitions. Keep role-to-permission assignments **out of** the official seed data until the Attorney's permissions are validated. Development-only fixtures must be clearly labeled. |
| D5 | Conservative, configurable technical defaults for password length, session expiry, and login throttling, documented as provisional. |
| D6 | Work in the real project directory with version history (Claude Code was chosen). |

## 2. Milestone plan

| # | Milestone | Status |
|---|---|---|
| 1 | Project skeleton, configuration, database connection, custom user model foundation | **Done, awaiting review** |
| 2 | Authentication and authorization | Next |
| 3 | Client management | |
| 4 | Request and document management | |
| 5 | Templates and document preparation | |
| 6 | Review, printing, and signing | |
| 7 | Archiving and OCR | |

Note: the custom user model had to be created in Milestone 1 (it cannot be changed safely after
the first migration), so ROLES and USERS exist now. PERMISSIONS and ROLE_PERMISSIONS arrive with
authorization.

## 3. Provisional settings (D5): not office policy

All are environment variables with these development defaults.

| Setting | Default | Used from |
|---|---|---|
| `PASSWORD_MIN_LENGTH` | 12 | Milestone 1 (validator configured) |
| `SESSION_IDLE_TIMEOUT_SECONDS` | 1800 (30 minutes, restarts on each request) | Milestone 1 |
| `LOGIN_MAX_ATTEMPTS` | 5 | Milestone 2 |
| `LOGIN_LOCKOUT_MINUTES` | 15 | Milestone 2 |
| `TIME_ZONE` | `UTC` in code. `.env.example` suggests `Asia/Manila` | Milestone 1 |

Sessions also end when the browser closes. No absolute session lifetime is set.

## 4. How the code differs from, or adds to, the schema checkpoint

| Topic | What was done | Why |
|---|---|---|
| `last_login` | Deliberately **not** created. | The USERS schema has no such column. Login events will go to ACTIVITY_LOGS. |
| Foreign keys | Django creates them as `NO ACTION, DEFERRABLE INITIALLY DEFERRED`, and Django's `PROTECT` blocks deletion in the application. | The checkpoint says `ON DELETE RESTRICT`. The effect is the same (deletion is refused), but the database check happens at commit time. |
| Username uniqueness | A normal unique constraint **and** a case-insensitive unique index. | Django requires a plain unique constraint on the username field. The index enforces the checkpoint's case-insensitive rule. |
| Django built-in tables | `auth_permission`, `auth_group`, `django_session`, `django_content_type`, `django_migrations` exist. | These are framework tables. `auth_permission` and `auth_group` are **unused**. The system's own ROLES/PERMISSIONS/ROLE_PERMISSIONS are the only authority (PD-F). |
| `createsuperuser` | Disabled on purpose. | There is no superuser concept. The Attorney account comes from the setup command. |
| Django admin | Not installed. | It would create a second, unplanned way to manage users and permissions. |

## 5. Unresolved items that affect this foundation

| ID | Item |
|---|---|
| X-UQ-008 | Hosting. Until decided, HTTPS-related settings are environment-controlled (secure by default in production), and static-file serving in production is undecided. |
| X-UQ-009 | Backup and recovery for the database and the `storage/` folder. |
| X-PD-002 | Who performs the initial Attorney setup. |
| A-01 | The office's time zone. `Asia/Manila` in `.env.example` is an assumption to confirm. |
| X-TF-001/002 | Rich-text editor and DOCX fidelity. Not part of this milestone. |

## 6. Known limitations

- The home page and health check are public until authentication exists (Milestone 2).
- `/health/` is intentionally minimal. It reports only `ok` or `unavailable`.
- Static files are served only by the development server. Production static serving depends on hosting.
- The test suite needs a PostgreSQL user allowed to create databases.
