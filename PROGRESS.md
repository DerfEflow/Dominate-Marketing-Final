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

## ✅ DEPLOYED & LIVE (2026-06-10)
The app is **live on Railway, connected to Supabase**, admin login verified.
- Live URL: **https://web-production-9c290.up.railway.app** (login → dashboard OK)
- Project: **`just-commitment`** (`7c36d08d-…`), env `production`. Both services
  **Online**: `web` (gunicorn) + `worker` (social_scheduler.py).
- Supabase (Dominate's own account, ref `mkdyppaheqedefikiwqq`, pooler URL):
  9 tables created, Alembic at head `c3d4e5f6a7b8`, admin `fredwolfe2000`
  (fredwolfe@gmail.com, admin=True) bootstrapped.
- All env vars set on BOTH services via the Railway CLI + a **project-scoped
  token** (read at runtime from git-ignored `railway-token.txt`): SESSION_SECRET,
  DATABASE_URL (password URL-encoded — it contained `@`), DISABLE_BILLING,
  FLASK_ENV, OPENAI_API_KEY (current key — ROTATE recommended), OPENAI models,
  BOOTSTRAP_ADMIN_*, ADMIN_EMAIL, PUBLIC_BASE_URL.
- How the agent worked Railway with NO direct API write access: the project
  token is **read-only over GraphQL (mutations 403)**, but the **Railway CLI**
  (`RAILWAY_TOKEN=<project token>`) performs writes fine. `variable set --stdin
  --skip-deploys` then `redeploy --from-source`.

### Post-launch status (updated 2026-06-13)
- ✅ `lavish-joy` duplicate **DELETED by Fred** (no more failing deploys).
- ✅ `deploy-secrets.txt` **deleted** (DB+admin passwords no longer on disk).
- ⏳ **Rotate the OpenAI key** — still pending (it passed through chat). New key →
  set via Railway CLI (`railway variable set OPENAI_API_KEY --stdin ...`).
- ⏭️ **Volume** at `/app/static/uploads` — SKIPPED (project token can't create one;
  CLI panics/API 403; an orphaned empty `web-volume` may exist). App runs fine
  without it. Long-term fix for image persistence = Supabase Storage / S3, not a
  volume (see FEATURE_ROADMAP Phase 0.2).
- 📄 **`docs/FEATURE_ROADMAP.md`** written — full phased post-launch plan.

## 🔁 HANDOFF (2026-06-13) — Zapier MCP in progress; restart needed
Fred's directive: **automate the build to minimize his manual setup / mental-switch
energy.** App has NOT shipped; NO clients yet. He explicitly **does NOT want the
per-client approval-flow feature** — prioritize automating client onboarding/posting.
**Run in AUTONOMOUS BUILD MODE:** keep building to completion without stopping to ask;
make reasonable calls on soft questions and note them; only stop for HARD blocks
(money, going live, his keys, another app's account); **report once at the very end**
(essentials + numbered choices). This is Fred's standing build preference.
- **In progress:** connecting **Zapier MCP** so the agent can automate posting setup.
  Fred is creating a server at mcp.zapier.com and will save its (secret) URL to
  git-ignored `zapier-mcp-url.txt`. Next session registers it:
  `claude mcp add zapier "<url-from-file>" --transport http --scope local`
  then **restart the session** so the Zapier tools load.
- **Architecture caveat:** the Zapier MCP connects Zapier to the **agent (builder)**,
  NOT to the deployed app. The app's 24/7 autopilot posts via per-client **webhook
  URLs** (`_post_via_webhook` in `services/social_media_integration.py`) or native
  OAuth — keep that runtime path separate from the agent's MCP tools.
- **Open Q (unanswered):** which platforms to target first (FB Pages / IG / LinkedIn / X)?
- Paste-ready kickoff for the fresh session: **`docs/NEW_INSTANCE_KICKOFF.md`**.

---

## (historical) Railway deploy DIAGNOSIS — 2026-06-10
- Goal: deploy to Railway so images post and the autopilot runs 24/7.
- Code is pushed to GitHub `main`. Deploy config hardened:
  `railway.toml` has `preDeployCommand` (`flask db upgrade` + `flask
  bootstrap-admin`, FLASK_APP inline); Playwright build step made **non‑fatal**.
- Supabase for THIS app is a **fresh, EMPTY** project in a **different Supabase
  account** than the one connected to the Supabase MCP here (so no `flask db
  stamp` needed — empty DB builds itself).

### ROOT CAUSE FOUND (via GitHub deployment records — no Railway access needed)
There are **TWO Railway projects both connected to this one GitHub repo**, and
they behave OPPOSITELY on the *identical commit*:
- **`just-commitment`** — project `7c36d08d-8fc0-412e-a784-3b92f93be5ef`
  (created 2026-06-10) → **DEPLOYS SUCCESSFULLY.** Full ~3.5 min build, goes
  live, passes the `/` healthcheck (so the app boots → it HAS working
  SESSION_SECRET + a reachable DB). **THIS IS THE GOOD ONE — keep it.**
  Dashboard: https://railway.com/project/7c36d08d-8fc0-412e-a784-3b92f93be5ef
- **`lavish-joy`** — project `12b07053-6acc-4624-9620-8a9f1da5c7ec`
  (the ORIGINAL, since 2026-05-09) → **FAILS EVERY TIME**, in ~100s (too fast to
  finish a real build → broken at Railway *project-settings* level, NOT code).
  This is the duplicate Fred was staring at. **Delete it (with Fred's OK).**
  Dashboard: https://railway.com/project/12b07053-6acc-4624-9620-8a9f1da5c7ec
- The old PROGRESS note ("error deploying from source / no logs") was the
  `lavish-joy` symptom. Source access was never the problem — `railway-app[bot]`
  clones the repo fine (it reports exact commit SHAs to GitHub).

### Code fix shipped 2026-06-10 (commit 9443f39)
Removed leftover `pyproject.toml` + `uv.lock` (Replit `uv` files). `pyproject`
was missing Flask-Migrate/playwright/holidays, so any build via the uv path
would crash at `flask db upgrade`. Now `requirements.txt` is the only source of
truth. (Did NOT fix lavish-joy → confirms lavish-joy is a project-config issue.)

### NEXT (all Railway-dashboard clicks — Fred-only, agent has no Railway access)
1. In Railway, confirm which project name maps to `just-commitment`
   (`7c36d08d…`) and verify it has DATABASE_URL = the fresh Supabase URI +
   SESSION_SECRET + the OpenAI vars. Get its public URL → agent verifies it live.
2. Set `PUBLIC_BASE_URL` on just-commitment = its Railway URL; redeploy.
3. Turn on the **worker** process on just-commitment (Procfile `worker` line).
4. Add a **volume** at `/app/static/uploads` on just-commitment.
5. DELETE the failing `lavish-joy` duplicate (`12b07053…`) so it stops
   auto-deploying on every push.

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
