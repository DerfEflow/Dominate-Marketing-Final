# Dominate Marketing — Progress Note (2026-06-08)

Plain-English status so anyone (or a fresh Claude instance) can pick up cleanly.

## What this app is
Internal **salesperson tool** (pivoted from a B2C SaaS) that runs AI‑powered
social‑media marketing for local small businesses. The differentiated vision is
locked in **`docs/BLUEPRINT.md`** ("The Radar"): the AI never invents content —
it only turns **real, fresh research** (the business's website, trends, events,
news, competitors) into posts, so a small shop out‑markets the big competitor
with an agency. Never stale data.

## Where the code lives / git
- Working copy: `C:\Users\rjfla\Documents\Dominate Marketing\Dominate Marketing\domiMarket_fixed`
- Branch **`main`**, everything committed and **pushed** to GitHub
  `DerfEflow/Dominate-Marketing-Final`.
- Reference/recovery copy (NEVER edit): `...\domi2_extracted\domi2-replit-recovery`.

## Platform (LOCKED — do not change)
**Railway** (hosting) + **Supabase Postgres** (database). SQLite is the local‑dev
fallback. Flask‑Migrate owns the schema. **Not Vercel** (a Vercel connector
appeared in a session — ignore it).

## How to run locally
- Use the venv: `./venv/Scripts/python.exe`. gunicorn is Unix‑only; locally use
  `python main.py`.
- Port **5055** (5000/5001 are taken by Fred's other local apps — zombie procs).
  `PYTHONIOENCODING=utf-8 PORT=5055 ./venv/Scripts/python.exe main.py`
- Local admin login: **fredwolfe@gmail.com / localdev123**. `DISABLE_BILLING=true`.
- **AI is LIVE locally:** OpenAI key is in the git‑ignored `.env`;
  `OPENAI_TEXT_MODEL=gpt-5.5`, `OPENAI_IMAGE_MODEL=gpt-image-1-mini`.
- To restart cleanly (kill only THIS app's procs): PowerShell filter
  `CommandLine -like '*domiMarket_fixed*'` → Stop-Process.

## What's built & working (verified locally)
- Boots offline‑safe; all pages 200 with real data; salesperson login (email OR
  username); client CRUD with contact/retainer/status; billing UI muted.
- **The Radar engine** (`services/automation_engine.py` + `services/radar.py`):
  per‑client cycle = Profile → gather real signals → grounded plan → write +
  8‑criteria quality gate → schedule → post → refresh. Runs in simulation with
  no connectors; uses real APIs when present.
- **Client Profile** built by **rendering the site in a headless browser
  (Playwright)** + **GPT‑5.5 vision** reading a screenshot + text scrape.
- Radar feeds live now (no key): events/holidays, Google Trends (best‑effort),
  **Google News headlines**, competitor website. Dormant (need keys):
  Yelp/Maps reviews, sports/movie/concert events.
- **AI image generation** in posts (Plus tier+); **video** scaffold (Pro, dormant
  pending a provider key); tier gating via `brand.subscription_tier`.
- **Zapier webhook posting** connector (real posting without platform dev apps);
  simulated posting otherwise. Background scheduler ticks the engine.
- Docs: `docs/BLUEPRINT.md`, `docs/automation_engine.md`, `docs/DEPLOY_RUNBOOK.md`,
  `ROADMAP.md`, `DECISIONS.md`, `docs/architecture|data_model|env_template.md`.

## WHERE WE ARE RIGHT NOW — Railway deploy (in progress, BLOCKED)
- Goal: deploy to Railway so images post and the autopilot runs 24/7.
- Code is pushed to GitHub `main`. Deploy config hardened:
  `railway.toml` has `preDeployCommand` (`flask db upgrade` + `flask
  bootstrap-admin`, FLASK_APP inline); Playwright build step made **non‑fatal**.
- Supabase for THIS app is a **fresh, EMPTY** project in a **different Supabase
  account** than the one connected to the Supabase MCP here (so no `flask db
  stamp` needed — empty DB builds itself).
- Railway service: **"Dominate-Marketing-Final"** in project
  **"determined-inspiration"**, ~11 variables set, changes staged ("Apply 14
  changes"). **Deploy is failing: "There was an error deploying from source"**,
  with no build logs surfaced yet. NEXT: get the actual Build/Deploy log to
  diagnose (suspects: GitHub source access, branch/root‑dir setting, or build).

## ⚠️ SAFETY SITUATION (important)
Fred is running **4 Claude Code instances in parallel** on 4 apps, and may have
granted **broad/"full access"** to one or more. His apps **share accounts**: one
Supabase login (holds `truline-estimator`, `coating-log`, `octopus-write`,
`story-vista` — NONE is Dominate Marketing's DB), one Railway login, one GitHub.
Railway's **own built‑in "Agent"** was seen roaming into another app ("Delta
Coating"). Rule for THIS instance: **only ever touch Dominate Marketing.** Never
modify another app's Supabase project or Railway service. Prefer asking before any
shared‑account or destructive action.

## Required env vars on Railway (values are Fred's)
`DISABLE_BILLING=true`, `FLASK_ENV=production`, `OPENAI_API_KEY`,
`OPENAI_TEXT_MODEL=gpt-5.5`, `OPENAI_IMAGE_MODEL=gpt-image-1-mini`,
`BOOTSTRAP_ADMIN_USERNAME`, `BOOTSTRAP_ADMIN_PASSWORD`, `BOOTSTRAP_ADMIN_EMAIL`,
`ADMIN_EMAIL`, `SESSION_SECRET`, `DATABASE_URL` (Supabase URI). After first deploy
add `PUBLIC_BASE_URL` (the Railway URL). Turn on the **worker** process + a
**volume** at `/app/static/uploads`.

## Deferred to launch (each needs a key/$ or a Fred decision)
Rotate the OpenAI key (it passed through chat); real admin password; social
OAuth/Zapier zaps for real posting; review/event API feeds; video provider key;
a scraping API for blocked sites.
