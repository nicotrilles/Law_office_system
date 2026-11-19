# Jumamil Law System

Web-based legal document archiving and tracking system with OCR integration for Jumamil Law Office.
Internal use only. Roles: Office Staff and Attorney (clients have no accounts).

**Status:** Milestone 1 (project foundation). See `docs/DEVELOPMENT_NOTES.md` for decisions, the
milestone plan, provisional settings, and notes on the logical schema checkpoint (v1.3).

## Requirements

- Python 3.12 (Django 5.2 supports 3.10 to 3.13)
- PostgreSQL 16 or newer
- Git

## First-time setup

### 1. Virtual environment and dependencies

Windows (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements\dev.txt
```

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements/dev.txt
```

### 2. Create the database and a database user

Open `psql` (or pgAdmin's query tool) as the PostgreSQL administrator and run:

```sql
CREATE ROLE jumamil_app LOGIN PASSWORD 'choose-a-strong-password' CREATEDB;
CREATE DATABASE jumamil_law OWNER jumamil_app;
```

`CREATEDB` is needed **only on your development machine**, because Django's test runner creates a
temporary test database. A production database user should not have it.

### 3. Configure the environment

```
copy .env.example .env        (Windows)      cp .env.example .env        (macOS/Linux)
```

Edit `.env`: set `SECRET_KEY`, put your real password in `DATABASE_URL`, and set `TIME_ZONE` to the
office's time zone. **Never commit `.env`.** It is already listed in `.gitignore`.

Generate a secret key with:

```
python -c "from django.core.management.utils import get_random_secret_key as g; print(g())"
```

### 4. Create the tables and verify

```
python manage.py migrate
python manage.py check_database
python manage.py test
python manage.py runserver
```

Then open http://127.0.0.1:8000/ and http://127.0.0.1:8000/health/.

## Project layout

```
config/            settings (base / dev / prod), root URLs
apps/core/         shared pieces: error pages, health check, base model, check_database command
apps/accounts/     ROLES and USERS (custom user model). Login and permissions come in Milestone 2.
templates/ static/ shared page layout and CSS
storage/           future document storage. Git-ignored and never served by a URL.
logs/              rotating application log. Git-ignored.
docs/              development notes (decisions, milestones, schema deviations)
```

## Rules this project follows

- Secrets come from environment variables or the git-ignored `.env`, never from source code.
- The app refuses to start without `SECRET_KEY`. Production settings refuse to start without `ALLOWED_HOSTS`.
- Error pages are generic. Technical details go to `logs/app.log` only.
- Uploaded documents will never be stored in a publicly served folder.
- Database tables follow the provisional logical schema checkpoint. Each module's tables are
  created when that module is built.
- Notarial registration details (Doc. No., Page No., Book No., Series of) are entered manually by
  staff. The system never generates, reserves, or rolls over these numbers, and it is not a
  replacement for the Attorney's physical Notarial Register.
- OCR results are suggestions until a staff member verifies them. Original scans are preserved
  unchanged.

## Requirements and design documents

The requirements and design live in separate documents. Keep them in the repository (for example
under `docs/`) and treat them as the reference:

- Systems Analysis and Development Handoff Document (v1.1): requirements and confirmed decisions
- Logical Schema Checkpoint (v1.3): provisional database design and open questions
- Status Transition Model (v0.3): draft document workflow
