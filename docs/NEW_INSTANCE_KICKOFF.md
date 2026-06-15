# Kickoff prompt — Dominate Marketing (paste into a fresh Claude Code instance)

Open a new Claude Code instance pointed at the repo
(`C:\Users\rjfla\Documents\Business App Suite\Dominate Marketing\Dominate Marketing\domiMarket_fixed`)
and paste **everything below the line** as your first message.

---

You are taking over the **Dominate Marketing** app. You have no memory of prior
sessions — everything you need is in the repo and this prompt.

## 0. FIRST — read these, then confirm you're oriented
In order: **`PROGRESS.md`** (root — current status incl. the LIVE deploy + the
Zapier MCP handoff), **`docs/FEATURE_ROADMAP.md`** (the full phased post-launch
plan), **`docs/BLUEPRINT.md`** (locked vision — "The Radar"), `DECISIONS.md`,
`ROADMAP.md`. `CLAUDE.md` auto-loads the rest. Then tell Fred in 3–4 plain
sentences what the app is, that it's **already live**, and what we're doing next.

**Repo path** (it was moved into the Business App Suite):
`C:\Users\rjfla\Documents\Business App Suite\Dominate Marketing\Dominate Marketing\domiMarket_fixed`
Always run git **inside `domiMarket_fixed`** — the parent folder has a stray empty
git repo; ignore it. Branch `main`, pushed to `DerfEflow/Dominate-Marketing-Final`.

## 1. CURRENT STATUS — it's LIVE
Deployed on **Railway + Supabase**: https://web-production-9c290.up.railway.app
(admin login works; `web` + `worker` services online; AI on gpt-5.5). The deploy
that was previously "stuck" is fully resolved. No clients yet; app has not shipped
to real users.

## 2. YOUR ACCESS (verified — what you can and can't do)
- **GitHub:** `gh` CLI is authed as **DerfEflow** (repo + workflow scopes). Read
  and push to the repo directly.
- **Railway:** a **project-scoped token** at git-ignored `railway-token.txt`. It is
  **read-only over Railway's GraphQL API** (mutations return HTTP 403), but the
  **Railway CLI writes fine** with it. Pattern:
  `export RAILWAY_TOKEN="$(tr -d '\r\n' < railway-token.txt)"` then
  `railway variable set KEY --stdin --service web --environment production --skip-deploys`
  (value via stdin — never in argv) and `railway redeploy --service web --yes --from-source`.
  Services: `web` + `worker`. Scoped to the **just-commitment** project ONLY
  (`7c36d08d-…`), so it cannot reach Fred's other apps. **Volume creation is the one
  thing it can't do** (CLI panics / API 403) → Fred does that in the dashboard.
- **Zapier MCP:** being connected (see §4). After a session restart, Zapier tools
  (`mcp__…zapier…`) should be available. The MCP connects Zapier to **you (the
  builder)** — NOT to the deployed app.
- **Supabase:** Dominate's DB lives in a **separate Supabase account that is NOT
  connected** to the Supabase MCP in this environment. The connected Supabase MCP
  holds Fred's **OTHER** apps (`truline-estimator`, `coating-log`, `octopus-write`,
  `story-vista`) — **NEVER touch them.** To inspect Dominate's DB, connect with
  `psycopg2` via the **IPv4 pooler** host `aws-1-us-west-2.pooler.supabase.com:5432`
  (the DB password contains `@` → pass as a psycopg2 kwarg, or URL-encode `%40`).
  `DATABASE_URL` lives on Railway, not in a local file (deploy-secrets.txt was deleted).

## 3. SAFETY (Fred runs several Claude instances in parallel)
Shared accounts: one GitHub, one Railway login, one Supabase login. **Work on
Dominate Marketing ONLY.** Never modify another app's Railway service or Supabase
project. Railway's built-in "Agent" is NOT you. Ask before destructive or
shared-account actions. Secrets on disk are all git-ignored
(`railway-token.txt`, `DOMINATE-MArketing session secret.txt`, `zapier-mcp-url.txt`).

## 4. IMMEDIATE TASK — finish wiring Zapier MCP, then automate posting setup
1. Fred created a Zapier MCP server at mcp.zapier.com and saved its (secret) URL to
   git-ignored **`zapier-mcp-url.txt`**.
2. Register it (read the URL from the file at runtime, do NOT echo it):
   `claude mcp add zapier "<url>" --transport http --scope local`
   (`--scope local` keeps the tokenized URL out of the repo and limits it to this app.)
3. If the Zapier tools aren't visible yet, ask Fred to **restart the session** / run `/mcp`.
4. Then use the Zapier tools to **automate per-client posting setup** and **test-fire
   a post end-to-end**. Confirm what landed.
- **Architecture caveat (important):** the deployed app's autopilot posts at runtime
  via per-client **webhook URLs** (`_post_via_webhook` in
  `services/social_media_integration.py`) or native OAuth — that is separate from
  your MCP tools. The MCP is for automating *setup/testing*, not the app's runtime.

## 5. HOW FRED WORKS (important)
Non-coder. You run all commands yourself with full paths. Be **autonomous** — make
sensible calls, don't stop for soft questions; only stop for **hard blocks** (spending
money, going live, his keys/credentials, another app's shared account). Report in
plain English: essentials + **numbered choices with a recommendation**; he replies
with a number.
- **Direction Fred set 2026-06-13:** automate the build to minimize his manual setup
  and mental-switch energy. He **does NOT want the per-client approval-flow feature** —
  prioritize **automating client onboarding/posting**.
- **Open question he hasn't answered:** which platforms to target first
  (Facebook Pages / Instagram / LinkedIn / X)?

## 6. RUN LOCALLY to verify
venv: `./venv/Scripts/python.exe` (gunicorn is Unix-only; locally use `python main.py`).
Port **5055** (5000/5001 are taken by Fred's other local apps):
`PYTHONIOENCODING=utf-8 PORT=5055 ./venv/Scripts/python.exe main.py`. Kill ONLY this
app's procs via PowerShell filter `*domiMarket_fixed*`. Local admin (throwaway, in
git-ignored `.env`): fredwolfe@gmail.com / localdev123.

## 7. FOLLOW-UPS (noted, not blocking)
- **Rotate the OpenAI key** (it passed through chat) — set a fresh one via the
  Railway CLI when Fred provides it.
- Persistent image storage (Supabase Storage / S3) — the Railway volume couldn't be
  created; see `docs/FEATURE_ROADMAP.md` Phase 0.2.
- Full feature backlog (real posting → expand Radar feeds → analytics/learning →
  scale → video → polish) is in `docs/FEATURE_ROADMAP.md`.

Start with §0, then do §4.
