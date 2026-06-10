# Kickoff prompt — Dominate Marketing (paste this into a fresh Claude Code instance)

Open a new Claude Code instance **pointed at**
`C:\Users\rjfla\Documents\Dominate Marketing\Dominate Marketing\domiMarket_fixed`
and paste everything below as your first message.

---

You are taking over the **Dominate Marketing** app. You have no memory of prior
sessions — everything you need is in the repo.

## 0. FIRST: read these, then confirm you understand the state
1. Read **`PROGRESS.md`** (repo root) — the full current status, including exactly
   where the Railway deploy is stuck.
2. Skim **`docs/BLUEPRINT.md`** (the locked product vision — "The Radar"),
   **`DECISIONS.md`**, and **`ROADMAP.md`**. `CLAUDE.md` auto‑loads the rest.
Then tell Fred, in 3–4 plain sentences, what this app is and what the current
blocker is — so he knows you're oriented.

## 1. CRITICAL SAFETY RULES (Fred runs several Claude instances in parallel)
- **You work on Dominate Marketing ONLY.** Fred has 4 apps under **shared
  accounts** (one Supabase login, one Railway login, one GitHub). His other
  Supabase projects are `truline-estimator`, `coating-log`, `octopus-write`,
  `story-vista` — **never touch any of them.** Dominate Marketing's own Supabase
  is in a *different* Supabase account not connected here.
- **Never modify another app's database or Railway service.** If a tool/connector
  could affect a shared account, **ask Fred before acting.**
- Railway has its own built‑in "Agent" — that is NOT you; if it's running, Fred
  should stop it. You guide Railway via Fred's clicks; you have no Railway access.
- Work only in this folder. Branch is **`main`**, pushed to GitHub
  `DerfEflow/Dominate-Marketing-Final`. Commit after each chunk; push only when
  Fred asks (he asked for deploy, so pushing deploy fixes is expected).

## 2. PLATFORM LOCK
**Railway** + **Supabase Postgres** (SQLite local fallback, Flask‑Migrate). Do
**not** switch platforms. Ignore any Vercel connector.

## 3. HOW FRED WORKS
He is a **non‑coder**. You (the agent) run all commands yourself, with full
paths. Operate **autonomously** — make sensible engineering calls and keep going
— but **stop for hard blocks**: spending money, going live, his keys/credentials,
acting outside this app, or anything touching another app's shared account.
Report in plain English: the essential thing + **numbered choices with a
recommendation**; he replies with a number. Don't dump technical detail.

## 4. RUN IT LOCALLY (to verify changes)
- venv: `./venv/Scripts/python.exe`. Locally use `python main.py` (gunicorn is
  Unix‑only). Port **5055** (5000/5001 are taken by his other local apps).
  `PYTHONIOENCODING=utf-8 PORT=5055 ./venv/Scripts/python.exe main.py`
- Kill only THIS app's procs via PowerShell filter `*domiMarket_fixed*`.
- Local admin: **fredwolfe@gmail.com / localdev123**. AI is live (`.env`,
  gpt‑5.5). All pages should return 200; the demo client is "Bright Ideas
  Lighting."

## 5. YOUR IMMEDIATE TASK — finish the Railway deploy
The deploy is failing with **"There was an error deploying from source"** and no
build logs surfaced yet (see PROGRESS.md "WHERE WE ARE RIGHT NOW").
1. Get Fred to open the failed deployment in Railway and read you the **Build
   Logs / Deploy Logs** (or the red notifications). You cannot see Railway —
   guide him click‑by‑click and interpret what he reports.
2. Diagnose & fix. Likely suspects, in order: Railway↔GitHub **source access**
   for this repo; wrong **branch** (must be `main`) or **root directory** (must
   be repo root); then the **build** itself (the Playwright browser install is
   already made non‑fatal in `railway.toml`).
3. The Supabase DB for this app is **fresh and empty** → no `flask db stamp`
   needed; the `preDeployCommand` runs `flask db upgrade` to build tables.
4. After a green deploy: set `PUBLIC_BASE_URL` to the Railway URL, turn on the
   **worker** process, add a **volume** at `/app/static/uploads`, then log in and
   verify. (Full steps in `docs/DEPLOY_RUNBOOK.md`.)

## 5b. Hard blocks to bring back to Fred (don't do alone)
Spending money / upgrading paid resources; the live deploy decision itself;
rotating/exposing his real keys (note: his OpenAI key passed through chat earlier
— recommend he rotate it); anything touching another app's shared Supabase/
Railway/GitHub.

## 6. After launch (his blueprint backlog, each needs a key or decision)
Social OAuth/Zapier real posting; Yelp/Maps + events API feeds; a video provider
key (Pro tier); a scraping API for sites that block the headless browser.

Start by doing §0, then help Fred get the Railway deploy unstuck.
