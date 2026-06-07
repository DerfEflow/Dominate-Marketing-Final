# Architecture

Dominate Marketing is a server-rendered Flask app. It started as a public B2C
marketing-automation SaaS and is mid-pivot into a **private internal tool for
Fred's salespeople**.

## Big picture

```
Browser
  │  (HTML over HTTPS)
  ▼
Flask app (main_app.py: create_app)  ──►  Jinja2 templates (templates/) + Bootstrap (static/)
  │
  ├─ Blueprints (registered in create_app):
  │    auth                – login/signup/Google OAuth (auth.py)
  │    dashboard           – brands(clients)/campaigns/analytics (dashboard.py)
  │    admin               – admin console, user/salesperson mgmt (admin.py)
  │    marketing_strategy  – website analysis → strategy (marketing_strategy.py)
  │    payments / payment_routes – Stripe (dormant in internal mode)
  │    trend_api, sell_profile_api, quality_api, licensing_api – JSON APIs (services/)
  │
  ├─ services/  – the heavy lifting: AI clients, web scraping, trend research,
  │               campaign generation, quality control. Most talk to external
  │               APIs (OpenAI/Anthropic/Google/Stripe) and are DORMANT until
  │               keys are provided. They degrade gracefully when unconfigured.
  │
  └─ Data layer: SQLAlchemy models (models.py) + Flask-Migrate (migrations/)
       Local dev = SQLite fallback. Prod = Supabase Postgres via DATABASE_URL.
```

## Entry points
- `main_app.py` — the app factory (`create_app`) and the module-level `app`.
  Also registers the `flask bootstrap-admin` CLI command.
- `main.py` — thin local runner (`python main.py`, reads `PORT`, default 5000).
- Production: `gunicorn main_app:app` (see `Procfile` / `railway.toml`).

## The pivot (B2C → internal tool)
- `User.is_salesperson` / `User.is_admin` flags; admins provision users.
- `DISABLE_BILLING=true` + `billing_disabled()` mute all pricing/subscription UI.
- `main_app.py` has a `before_request` guard that redirects internal users (and
  everyone, when billing is disabled) away from billing/pricing routes. Stripe
  blueprints stay registered but dormant, so the SaaS path can be revived later.
- `Brand` is relabeled "Client" in the internal UI and carries contact/retainer
  fields for a salesperson's book of business.

## Boot safety (added during the autonomous pass)
Several `services/` modules used to create API clients or hit the network at
import time, which crashed boot when keys/packages were missing. These are now
lazy/guarded so the app boots fully offline with all paid integrations dormant:
- `marketing_strategy_agent.py`, `viral_tools_researcher.py` — Google Trends
  client created lazily on first use, not at import.
- `marketing_strategy_agent.py` — selenium imports guarded (optional tier).
- `natural_language_client.py`, `vision_api_client.py` — google-cloud imports guarded.

## Key routes (server-rendered)
- Public: `/`, `/features`, `/faq`, `/terms`, `/privacy`, `/auth/login`.
- Dashboard (`/dashboard/...`): index, brands, brand/create, campaign/create,
  brand/<id>/new_campaign, campaign/<id>, campaign/<id>/status, analytics,
  gallery, social, scheduling, ai-status, tone-examples.
- Admin (`/admin/...`): dashboard, users, salespeople, reports, communications,
  quality-control.
