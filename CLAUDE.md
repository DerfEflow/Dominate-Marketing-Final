# Dominate Marketing
Internal salesperson tool (mid-pivot from B2C SaaS). Flask + Postgres/SQLite + Flask-Migrate.

Run locally (Windows): create/activate venv, `pip install -r requirements.txt`,
set `FLASK_APP=main_app:app` and a local sqlite `DATABASE_URL`, run `flask db upgrade`,
then `python main.py` → http://localhost:5000 (use a different PORT if 5000 is taken
by another local app — see DECISIONS.md).

PLATFORM IS LOCKED: Railway (hosting) + Supabase Postgres (database). Do not change the platform.
On Windows, gunicorn does not run — use `python main.py` locally; gunicorn is prod-only.

The product's differentiated vision is in docs/BLUEPRINT.md — the engine creates
content ONLY from real, fresh research (The Radar), never AI invention.

@docs/BLUEPRINT.md
@docs/automation_engine.md
@docs/architecture.md
@docs/data_model.md
@docs/env_template.md
