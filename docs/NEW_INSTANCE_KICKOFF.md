# Kickoff prompt — Dominate Marketing (paste into a fresh Claude Code instance)

Open a new Claude Code instance pointed at the repo
(`C:\Users\rjfla\Documents\Business App Suite\Dominate Marketing\Dominate Marketing\domiMarket_fixed`)
and paste **everything below the line** as your first message.

---

You are taking over the **Dominate Marketing** app. You have no memory of prior
sessions — everything you need is in the repo and this prompt.

## 0. FIRST — read, then confirm you're oriented
Read in order: **`PROGRESS.md`** (root — current status, what just shipped, the
foundational TODO), **`docs/FEATURE_ROADMAP.md`** (full phased plan),
**`docs/BLUEPRINT.md`** (locked vision — "The Radar"), `DECISIONS.md`. `CLAUDE.md`
auto-loads the rest. Then tell Fred in 3-4 plain sentences what the app is, that
it's LIVE and already posting real grounded content, and what we're building next.

**Repo path** (moved into the Business App Suite):
`C:\Users\rjfla\Documents\Business App Suite\Dominate Marketing\Dominate Marketing\domiMarket_fixed`
Always run git **inside `domiMarket_fixed`** (the parent has a stray empty git repo;
ignore it). Branch `main` → `DerfEflow/Dominate-Marketing-Final`.

## 1. STATUS — live and posting for real
- Deployed on **Railway + Supabase**: https://web-production-9c290.up.railway.app
  (admin login works; `web` + `worker` services online; AI on gpt-5.5).
- **Real posting works end-to-end (proven):** the engine researched
  trulineroofing.com → wrote a grounded caption → generated a compliant image →
  **published to the Facebook Page "5 Prime Roof Coating Consultants"** via Zapier.
- No paying clients yet; Truline is the first live client (Fred's own business).

## 2. YOUR ACCESS (what you can / can't do)
- **GitHub:** `gh` authed as **DerfEflow** (repo+workflow). Push directly.
- **Railway:** project-scoped token in git-ignored `railway-token.txt`. READ-ONLY
  over Railway's GraphQL API (mutations → 403) but the **CLI writes fine**:
  `export RAILWAY_TOKEN="$(tr -d '\r\n' < railway-token.txt)"` then
  `railway variable set KEY --stdin --service web --environment production --skip-deploys`
  and `railway redeploy --service web --yes --from-source`. Services: `web`,`worker`.
  Scoped to the **just-commitment** project only. (Volumes can't be made with this
  token — not needed; image hosting is Supabase Storage now.)
- **Zapier MCP** (real posting): authenticated HTTP/JSON-RPC endpoint. Creds in the
  wallet `~/.app-secrets.env` (`Zapier_MCP_DOMINATE`=URL, `Zapier_MCP_TOKEN`=bearer).
  Drive it with the git-ignored helper `scripts/zap_mcp.py` (e.g.
  `python scripts/zap_mcp.py list_enabled_zapier_actions '{}'`). Enabled apps:
  **Facebook Pages** (Create Page Post) + Roofr. NOT registered as a Claude Code MCP
  and doesn't need to be — call it over HTTP. NEVER fire write actions except when
  Fred explicitly approves (they post to his real page / create real roofing jobs).
- **Supabase Storage** (image hosting): Dominate's OWN Supabase (ref
  `mkdyppaheqedefikiwqq`), public bucket `post-media`. Service key in git-ignored
  `supabase-key.txt` (`sb_secret_...` format). Env `SUPABASE_URL`+`SUPABASE_SERVICE_KEY`
  set on web+worker.
- **Dominate's DB** is in a SEPARATE Supabase account NOT connected to the Supabase
  MCP here. The connected Supabase MCP holds Fred's OTHER apps
  (truline-estimator, coating-log, octopus-write, story-vista) — **NEVER touch them.**
  Inspect Dominate's DB with psycopg2 via the IPv4 pooler
  `aws-1-us-west-2.pooler.supabase.com:5432` (DB password has `@` → pass as a
  psycopg2 kwarg or URL-encode `%40`). `DATABASE_URL` lives on Railway.

## 3. SAFETY (Fred runs several Claude instances in parallel)
Shared accounts (one GitHub, one Railway, one Supabase login). **Work on Dominate
Marketing ONLY.** Never modify another app's Railway service or Supabase project.
Railway's built-in "Agent" is NOT you. All secrets on disk are git-ignored
(`railway-token.txt`, `supabase-key.txt`, `DOMINATE-MArketing session secret.txt`,
`zapier-mcp-url.txt`). Don't echo secret values.

## 4. HOW FRED WORKS — AUTONOMOUS BUILD MODE (his default for builds)
Non-coder; you run all commands with full paths.
- **Run the whole build to completion WITHOUT stopping to ask.** Make reasonable
  calls on soft questions, note them, keep going. This overrides "one step at a time."
- **Only stop for HARD blocks:** spending money, going live to real users / publishing
  public content, his keys/decisions, or anything touching another app's account.
  (Publishing a post to a real page DOES need his explicit OK each time.)
- **Report ONCE at the end** (or at a hard block): essentials + **numbered choices
  with a recommendation**; he replies with a number. Commit/push working chunks freely.
- Standing direction: **automate the build to minimize his manual setup / mental-switch
  energy.** He does NOT want a per-client approval-flow feature.

## 5. YOUR NEXT TASK — the foundational gap Fred flagged
> "It's supposed to have a comprehensive profile and marketing plan for each client."
The app must generate ALL client answers itself. Today the profile is shallow
(it missed Truline's **service area** → a post said "Central Ohio" from a news
headline) and there's **no persistent per-client marketing plan** (plans are
regenerated ephemerally each cycle in `automation_engine.build_plan`). Build:
1. **Deep client profile** — service area/geography, offers, audience, proof,
   differentiators, tone/voice, and **banned topics** — persisted on the Brand and
   editable in the UI. Extend `ensure_profile`/`_build_profile` in
   `services/automation_engine.py`.
2. **Persistent marketing plan per client** — a stored, living plan the Strategist
   maintains (not throwaway per-cycle ideas), surfaced + editable on the client page.
Goal: the salesperson never hand-answers what the app should already know.

## 6. HARD CONTENT RULE (Fred, important)
In generated images, **never render a person applying ROOF COATING** (AI renders
the coating tools/technique wrong). Traditional roofing work IS fine. This is in
`_image_prompt`; you can also vision-verify a generated image with `_openai_vision`.

## 7. How posting + media work now (so you don't re-derive it)
- A `SocialAccount` with `webhook_url == 'zapier-mcp'` posts via
  `services/zapier_mcp.py` (`_post_via_zapier_mcp` in `social_media_integration.py`);
  target page read from `account.platform_user_id`/`username`. No per-client Zap.
- Generated images upload to Supabase Storage (`services/storage.py`) → permanent
  public URL stored as the post's image_url → fetchable by Facebook/Zapier.
- **GPT-5.x token trap:** keep `max_completion_tokens` >= ~700 on generation calls
  or the model's reasoning eats the budget and returns empty (caused template
  fallbacks). Zapier execute: instruct it to "publish immediately, no follow-up
  questions" or it returns a clarifying question instead of posting.

## 8. RUN LOCALLY to verify
venv: `./venv/Scripts/python.exe` (gunicorn is Unix-only; locally `python main.py`).
Port **5055**: `PYTHONIOENCODING=utf-8 PORT=5055 ./venv/Scripts/python.exe main.py`.
Kill only `*domiMarket_fixed*` procs. Local admin: fredwolfe@gmail.com / localdev123.
On Git-Bash, set `MSYS_NO_PATHCONV=1` before passing `/app/...`-style paths to CLIs.

## 9. FOLLOW-UPS (noted, not blocking)
- **Rotate the OpenAI key** (passed through chat) — set a fresh one via the Railway CLI.
- Delete the 2 test posts on the 5 Prime FB Page (one "Testing…", one the Truline post).
- Per-client onboarding automation; Instagram/LinkedIn/X Zapier actions; pull-back
  metrics; real analytics + learning loop. Full plan: `docs/FEATURE_ROADMAP.md`.

Start with §0, then build §5.
