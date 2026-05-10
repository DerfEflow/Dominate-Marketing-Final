# Database Migrations

Dominate Marketing uses [Flask-Migrate](https://flask-migrate.readthedocs.io/)
(an Alembic wrapper) to manage Postgres schema changes. This document is the
practical operating manual.

## Why we have this

Until 2026-05-09 the app called `db.create_all()` at startup, which only
**creates missing tables** — it never adds columns to existing ones. The
moment we needed our first additive column change (the B2C → internal-tool
pivot), `create_all()` stopped being enough. Flask-Migrate replaces it.

`db.create_all()` has been removed from `main_app.py`. The schema is now
owned exclusively by the migration files in `migrations/versions/`.

## How it runs in production

Railway picks up the `release` line in `Procfile`:

```
release: flask db upgrade && flask bootstrap-admin
```

Every deploy:
1. `flask db upgrade` applies any pending migrations to the Supabase Postgres.
2. `flask bootstrap-admin` creates the first admin user from environment
   variables (idempotent — does nothing if an admin already exists).
3. The web process starts.

If the release step fails, Railway aborts the deploy and the previous version
keeps serving traffic. No partial-state risk.

## One-time prod setup (do this BEFORE the first deploy of this PR)

The production Supabase database already has every table from the baseline
migration. Alembic doesn't know that yet, so we have to tell it:

```bash
# From a Railway shell or anywhere with the prod DATABASE_URL set:
flask db stamp e8d2efaa80d1
```

This writes the baseline revision ID into the `alembic_version` table without
changing any data. After this, the next `flask db upgrade` will run only the
pivot migration (`f06038cdd1a2`), not the baseline.

**You only do this once.** If you forget, the first deploy will try to
`CREATE TABLE users` against tables that already exist and crash. Stamp first.

## Local development workflow

### First-time setup
```bash
pip install -r requirements.txt
export DATABASE_URL=sqlite:///dominate.db   # or your local Postgres URL
export FLASK_APP=main_app:app
flask db upgrade   # builds your local DB from the baseline + pivot
```

### Adding a schema change
1. Edit `models.py` (add a column, change nullability, etc.).
2. Generate the migration:
   ```bash
   flask db migrate -m "short description of the change"
   ```
3. **Read the generated file** in `migrations/versions/`. Alembic's autogen is
   good but not perfect — common things to fix by hand:
   - `NOT NULL` columns added to tables with existing rows must include
     `server_default=...` or the migration will crash on prod data.
   - Foreign-key constraints with `name=None` will cause headaches on
     subsequent drops in Postgres. Always give them an explicit name.
   - Autogen does NOT detect: column renames (it sees them as drop+add),
     CHECK constraints, or data-only migrations.
4. Test locally:
   ```bash
   flask db upgrade    # apply
   flask db downgrade  # roll back, confirm clean
   flask db upgrade    # re-apply
   ```
5. Commit the migration file alongside the `models.py` change.
6. Push. Railway runs `flask db upgrade` on deploy.

### Useful commands
```bash
flask db current       # which revision is the DB at?
flask db history       # list all migrations
flask db heads         # latest revision Alembic knows about
flask db stamp <rev>   # mark DB as being at <rev> without applying anything
flask db downgrade -1  # roll back one revision (local only — don't do this on prod)
```

## What's in the repo right now

```
migrations/
├── alembic.ini
├── env.py
├── README
├── script.py.mako
└── versions/
    ├── e8d2efaa80d1_baseline_schema_pre_pivot.py     # baseline
    └── f06038cdd1a2_pivot_to_internal_salesperson_tool.py
```

- **Baseline (`e8d2efaa80d1`):** snapshot of the schema before the internal
  pivot. Auto-generated against an empty DB.
- **Pivot (`f06038cdd1a2`):** adds `User.is_salesperson`, `User.is_admin`,
  `User.created_by_admin_id`; relaxes `User.email` to nullable; adds 8 client-
  contact columns to `Brand`. Hand-patched after autogen — see the
  `# MANUAL FIX` comments in the file for what changed and why.

## Things that will bite you

- **Don't run `db.create_all()` from anywhere.** The migration files are the
  source of truth. If you need a new table during development, write a
  migration and `flask db upgrade`, don't bypass.
- **Don't edit a committed migration.** Once a migration has been applied to
  any prod-like database, treat it as immutable. Write a new migration to
  fix mistakes.
- **Don't `flask db downgrade` against prod.** Schema rollbacks against live
  data lose information. If something goes wrong, write a forward migration.
- **The first deploy needs `flask db stamp` first** (see "One-time prod setup"
  above). The release command will fail otherwise.
