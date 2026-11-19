# Development Notes

Everything here is **provisional** unless explicitly marked confirmed. Nothing in this file is
confirmed office policy.

## 1. Approved decisions (project team review)
## APPROVED
| ID | Decision |
|---|---|
| D1 | Django 5.2 LTS, PostgreSQL, server-rendered pages. |
| D2 | Build incrementally. Create each module's tables when that module is built. The schema checkpoint (now v1.3) stays the provisional reference. |
| D3 | The initial Attorney account is created by a one-time command-line command with a securely prompted password. No default credentials. |
| D4 | Seed **only the two roles** (`Office Staff` and `Attorney`). Permission definitions and role-to-permission assignments **remain empty** in Milestone 2 (decision Q5). Assignments stay out of the official seed data until the Attorney's permissions are validated, and a permission definition is added only by the milestone whose features need it, after its keys are approved. Development-only fixtures must be clearly labeled. |
| D5 | Conservative, configurable technical defaults for password length, session expiry, and login throttling, documented as provisional. |
| D6 | Intended working method: work in the real project directory with version history (Claude Code). Milestone 1 itself was built in a chat session and delivered as a zip, so it has no version history until it is committed to the repository. |

## 2. Milestone plan

| # | Milestone | Status |
|---|---|---|
| 1 | Project skeleton, configuration, database connection, custom user model foundation | **Done, awaiting review** |
| 2 | Authentication and authorization | **In progress.** Stage 1 of 8 (housekeeping) delivered, awaiting review. See section 8. |
| 3 | Client management | |
| 4 | Request and document management | |
| 5 | Templates and document preparation | |
| 6 | Review, printing, and signing (includes manual entry of registration details) | |
| 7 | Archiving and OCR (includes OCR extraction of registration details, staff verification, and registration search) | |

Note: the custom user model had to be created in Milestone 1 (it cannot be changed safely after
the first migration), so ROLES and USERS exist now. PERMISSIONS and ROLE_PERMISSIONS arrive with
authorization (Milestone 2).

Numbering: the build order approved in D2 listed "database connection and initial migrations" as a
separate second item and authentication as the third. The first delivery combined the skeleton and the
database connection into Milestone 1, so authentication is **Milestone 2**. Earlier code comments that
said "Milestone 3" were corrected in Stage 1.

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
| `last_login` | Deliberately **not** created. | The USERS schema has no such column. Login events will be recorded in an activity log in a later milestone (the activity log is deferred, section 8). |
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
| X-UQ-023 | When registration details are entered relative to review, approval, and printing, and the effect on versions. **Resolve before Milestone 6.** |
| X-UQ-024 | What "relevant registration information" exists beyond the four fields, and whether all four must be complete. |
| X-UQ-025 | Whether the system records the Attorney's confirmation that the document matches the physical register entry. |
| X-UQ-011 / X-UQ-012 | Which document types require registration, and the correction procedure. |
| Audit trail | Deferred to a later milestone (Milestone 2 decision Q3). Until then, authentication events are written only to the technical server log, which is not tamper-evident. Failed sign-ins for unknown usernames cannot be stored in `ACTIVITY_LOGS` because `user_id` is required (X-UQ-018). |
| Password change and reset | No requirement says how a person changes a password, or how the Attorney recovers if locked out. Milestone 2 does not deliver this. A developer-run recovery procedure should be agreed before real use. |
| Assigning permissions to roles | No tool exists in Milestone 2 (D4). Before Milestone 3 can be used end to end, an approved assignment command or a clearly labeled development fixture is needed. |
| X-PD-001 / X-UQ-007 | Whether the Attorney manages users, and the real permission matrix. Nothing is assigned in Milestone 2. |

## 6. Known limitations

- The home page and health check are public until authentication exists (Milestone 2).
- `/health/` is intentionally minimal. It reports only `ok` or `unavailable`.
- Static files are served only by the development server. Production static serving depends on hosting.
- The test suite needs a PostgreSQL user allowed to create databases.

## 7. Notarial registration and OCR: constraints for later milestones (confirmed 16 November 2026)

No registration or OCR code exists yet (Milestone 1 contains only `ROLES` and `USERS`), so nothing in
the implementation conflicts with these decisions. They are recorded here so later milestones follow them.

**Must not be built (confirmed restrictions)**
- No automatic generation, reservation, or "suggest the next number" logic for Doc. No.
- No page or book rollover calculation.
- No OCR value treated as verified until a staff member verifies it.
- Nothing that presents the system as the official Notarial Register.

**Must be supported**
- Manual entry of Doc. No., Page No., Book No., and Series of (a calendar year, for example 2026) on a document. Never on a client or a request.
- No uniqueness constraint on Doc. No. (numbering restarts each year) or on Book No. plus Page No. (several entries share a page). A duplicate Series plus Doc. No. should only show a warning.
- OCR extraction of these fields as suggestions, staff verification and correction, and filtering by registration year, Doc. No., Page No., and Book No.
- The original scanned file is preserved unchanged.

**Where it fits**

| Work | Milestone | Depends on |
|---|---|---|
| Registration entry, printing, signing | 6 | X-UQ-023 answered first |
| OCR extraction, verification, registration search | 7 | Representative scans from the office for the OCR feasibility tests (X-TF-003, X-TF-004) |

**Permissions.** Permission keys are added by the milestone that uses them, so Milestone 2 seeds only
what it needs. Likely future keys (provisional names): `registration.record`, `registration.correct`,
`archive.verify_metadata`. Which role holds each stays unassigned until validated (D4, X-UQ-007).

**Recommendation (not a requirement).** Wherever registration details appear, show a short label such as
"Recorded copy. The official record is the physical Notarial Register." This keeps staff from mistaking
the system for the register.

**Proposed, not applied.** A four-digit-year CHECK on Series of and two search indexes are described as
P-1 and P-2 in the schema checkpoint, section 11B. They await approval and affect nothing built so far.

## 8. Milestone 2: approved plan (Revision 3)

The full plan is in `MILESTONE_2_PLAN.md`. This is the short record of what was approved. All technical
values remain provisional, and nothing here is confirmed office policy.

**Decisions**

| # | Decision | Outcome |
|---|---|---|
| Q1 | Failed-login counts stored in Django's database-backed cache | Approved |
| Q2 | Throttle key: username (any letter case) plus network address; fixed lock | Approved |
| Q3 | Activity log | **Deferred** to a later milestone |
| Q4 | Two management commands for accounts (`create_user`, `set_user_status`); no web user management yet | Approved |
| Q5 | Seed no permission definitions and no role-permission assignments | Approved |
| Q6 | The home page requires sign-in | Approved |
| Q7 | Refuse initial Attorney setup if any Attorney-role account exists, active or inactive | Approved |
| Q8 | Command names and behavior | Approved |
| Q9 | Composite primary key on `role_permissions` | Approved |
| Q10 | Documentation and milestone-numbering corrections | Approved (this Stage 1) |

**Details confirmed (D-1 to D-9, with four clarifications):** `create_user` refuses the Attorney role;
`set_user_status` refuses to deactivate the last active Attorney and locks the `Attorney` row of `roles`
first; a dedicated cache named `login_throttle`; the throttle fails closed; the username limit (50
characters) and full-name limit (150) are read from the model fields; the cache table is created by the
documented `createcachetable` step; the login view receives both `form_class=LoginForm` and
`template_name="accounts/login.html"`; test permission keys are temporary and the test registry is always
restored.

**Stages**

| Stage | Content | Status |
|---|---|---|
| 1 | Housekeeping: comments and documentation | Delivered, awaiting review |
| 2 | Permission tables and reference data | Not started |
| 3 | Initial Attorney setup command | Not started |
| 4 | Account administration commands | Not started |
| 5 | Login and logout | Not started |
| 6 | Login throttling | Not started |
| 7 | Authorization service and view guard | Not started |
| 8 | Protect the home page, final documentation, full verification | Not started |

Each stage ends with a review. The next stage does not start until the previous one is approved.
