# Environment variables

Mirror of `.env.example`. Copy `.env.example` → `.env` for local dev. **Never
commit a real `.env`.** On Railway, set these in the dashboard under Variables.

The app **boots and is fully reviewable with all of these blank** except
`SESSION_SECRET` (any value) and `DATABASE_URL` (defaults to local SQLite if
unset). Paid integrations stay dormant and show "not configured" states.

## Core
- `SESSION_SECRET` — Flask session signing key. Any random 32+ char string locally.
- `FLASK_ENV` — `development` locally, `production` on Railway.
- `DATABASE_URL` — Postgres connection string in prod (Supabase). If unset,
  falls back to `sqlite:///dominate.db`. The app auto-rewrites the
  `postgres(ql)://` prefix to `postgresql+psycopg2://`.
- `DISABLE_BILLING` — `true` to run as the internal tool (hides all
  pricing/subscription UI). Set to `true` for the internal-salesperson use case.

## First admin (CLI: `flask bootstrap-admin`)
- `BOOTSTRAP_ADMIN_USERNAME`
- `BOOTSTRAP_ADMIN_PASSWORD`
- `BOOTSTRAP_ADMIN_EMAIL` — log in with this **email** + the password.
Idempotent: does nothing if an admin already exists.

## AI services (dormant until set)
- `OPENAI_API_KEY` — https://platform.openai.com/api-keys
- `ANTHROPIC_API_KEY` — https://console.anthropic.com/
- `GOOGLE_API_KEY` — Google AI (video generation)
- `GOOGLE_APPLICATION_CREDENTIALS` — path to a Google Cloud service-account JSON
  (only needed for the optional Vision / Natural-Language features; those Python
  packages are also optional and not in requirements.txt).

## Google OAuth (optional login method)
- `GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_CLIENT_SECRET`
- `OAUTH_CALLBACK_URL` — full callback URL (set to your Railway domain at deploy).

## Stripe (dormant in internal mode)
- `STRIPE_SECRET_KEY`, `STRIPE_PUBLISHABLE_KEY`, `STRIPE_WEBHOOK_SECRET`
- `STRIPE_PRICE_BASIC`, `STRIPE_PRICE_PLUS`, `STRIPE_PRICE_PRO`, `STRIPE_PRICE_ENTERPRISE`

## Misc / optional
- `ADMIN_EMAIL` — admin contact address.
- `SERPAPI_KEY`, `GOOGLE_CUSTOM_SEARCH_CX` — enhanced trend research.
- `PIKA_LABS_API_KEY` — optional video service (status page only).
