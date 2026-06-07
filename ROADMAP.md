# Dominate Marketing — Roadmap

Goal: finish the pivot from a public **B2C SaaS** into a clean **internal tool
for Fred's salespeople**, and get it to a state Fred can review locally.

This file is the plan. See `DECISIONS.md` for the judgment calls made along the
way, in plain English.

---

## Current-state assessment (as found, then fixed)

**What works now (verified by running the app on local SQLite, no API keys):**
- App boots cleanly with every paid integration dormant (OpenAI/Anthropic/
  Google/Stripe/OAuth all off). It no longer crashes or makes network calls at
  startup.
- All 21 main pages return 200 (or the correct redirect): landing, features,
  faq, terms, privacy, login; the whole dashboard (clients, campaigns,
  analytics, gallery, social, scheduling, AI status, tone examples); and the
  whole admin console (dashboard, users, salespeople, reports, communications,
  quality control).
- Login works by **email or username** (admins by email, salespeople by username).
- Admin can provision a salesperson; that salesperson can log in and use the app.
- A campaign can be created (with or without a client attached) and its status
  page renders; generation degrades gracefully to "not configured" with no key.
- Billing/pricing UI is muted for internal users (`DISABLE_BILLING=true`).

**What was broken and got fixed (Phase 0 + early Phase 1):**
- Import-time crashes / network calls (selenium, Google Trends, google-cloud).
- ~9 pages threw 500s due to routes not passing variables their templates need.
- Campaign creation referenced endpoints and a DB column that didn't exist.
- Salespeople literally could not log in (login was email-only).

**Still half-pivoted / cosmetic (not blocking review):**
- Some templates still use B2C language ("Upgrade your plan", "Subscription
  Tier", pricing CTAs) even though billing is muted for internal users.
- "Brand" is the internal "Client", but the relabel isn't consistent everywhere.
- Admin reports still count internal accounts in customer metrics (TODO'd in code).

---

## Phased plan (biggest-unblock-for-least-effort first)

### Phase 0 — Make it run & boot clean  ✅ DONE
- Working branch, fresh venv, local SQLite DB via `flask db upgrade`, local admin.
- Lazy/guarded all import-time external clients so boot is offline-safe.

### Phase 1 — Make every page reviewable  ✅ DONE
- Fixed all page-level 500s (missing template variables, SQLite-incompatible
  queries, a missing template, and a SQLAlchemy 2.x `case()` bug).
- Repaired the campaign-creation flow end to end.
- Fixed salesperson login (email-or-username).

### Phase 2 — Finish the internal-tool experience  ✅ DONE
1. ✅ Stripped B2C/billing UI (tier badges, subscription status, upgrade CTAs)
   from the internal surfaces via the `hide_billing_ui` flag.
2. ✅ Relabeled "Brand" → "Client" across nav and the main dashboard pages.
3. ✅ Real client management: add/edit a client with contact name/email/phone,
   monthly retainer, status (active/onboarding/paused/churned), and internal
   notes. The client page now shows a contact card; the list shows status +
   contact + retainer. (This was previously impossible — the fields existed in
   the database but no form captured them.)
4. ◀ STILL OPEN (Fred's taste): what to do with the public marketing pages
   (landing/features/faq) for an internal-only tool — keep, simplify, or route
   straight to login. Left as-is for now; harmless.

### Phase 3 — Exercise the real features  ✅ MOSTLY DONE
1. ✅ Marketing-strategy pages (analyze / dashboard / create-campaign) render
   and degrade gracefully without AI keys.
2. ✅ Verified every page end-to-end WITH real data (not just empty states):
   admin + salesperson login, client create/view/edit, campaign creation,
   data isolation (salespeople see only their own clients), admin gating
   (salespeople are blocked from /admin).
3. ◀ STILL OPEN: admin reports still count internal accounts in customer
   metrics (the `is_salesperson/is_admin` filters are TODO'd in admin.py).
   Low priority while there are no real customers yet.

### Phase 3b — Known deferrals (not part of the salesperson MVP)
- The media-**licensing** feature (`/licensing/*`, `/api/license/*`) still
  errors on bad inputs. It is NOT linked anywhere in the internal UI, so
  internal users never reach it. Fix or remove if/when licensing is needed.
- The standalone `brand_detail` page was retired; its URL now redirects to the
  single canonical client page.

### Phase 3c — Automation Engine  ✅ BUILT (simulation-ready)
The product's core value loop, per client: **research → generate → schedule →
auto-post → continually refresh.** See `docs/automation_engine.md`.
- ✅ `services/automation_engine.py` orchestrates the full cycle and the
  continual-refresh driver.
- ✅ Runs end-to-end with NO keys/connectors (simulation): placeholder research,
  templated content, "connect (simulated)" accounts, SIMULATED posting. Same
  code uses real APIs/OAuth the moment Fred adds them.
- ✅ Client-scoped (accounts/research/posts/settings live on the Brand/client).
- ✅ Scheduler worker fixed (`process_due_posts`) + research-refresh pass; runs
  in-process locally and as the Railway `worker` in prod.
- ✅ "Marketing Autopilot" panel on each client page (toggle, cadence, run-now,
  freshness, connected accounts, upcoming posts).
- ✅ Verified hands-off in the live server: scheduled posts auto-publish on time.
- NEEDS FRED (Phase 4): real AI keys; real social OAuth apps (FACEBOOK/TWITTER/
  LINKEDIN/TIKTOK client id+secret); the Railway worker process running 24/7.

### Phase 4 — Pre-launch (Fred-owned hard blocks; do NOT do autonomously)
1. Real `SESSION_SECRET` + real admin credentials (env, never code).
2. Real API keys for the AI features Fred wants live.
3. Live Supabase Postgres `DATABASE_URL`; one-time `flask db stamp e8d2efaa80d1`
   before the first deploy (see MIGRATIONS.md), then deploy on Railway.
4. Persistent storage for `outputs/` and `static/uploads/` (Railway volume or
   object storage) — they're ephemeral on Railway today.
5. Rotate any secret that was ever committed (see DECISIONS.md secret-hygiene note).

---

## Known gaps / notes (not blocking local review)
- The per-tier client limit in `create_brand` reads `subscription_tier` directly.
  It works today because admins/salespeople are created as ENTERPRISE (limit 50),
  but it doesn't honor `billing_disabled()` like the model helpers do. Low risk.
- `services/` has many modules that need keys; they're dormant and guarded.
- Local dev runs `python main.py` (gunicorn is Unix-only; prod uses gunicorn).
