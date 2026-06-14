# Dominate Marketing — Feature Roadmap (post-launch)

*Written 2026-06-13. Plain-English, step-by-step. This is the path from "deployed
and working" to the full BLUEPRINT vision: one salesperson runs 100 clients, each
out-marketing their big competitor, on real fresh research — never invented content.*

## How to read this
- Phases are ordered **biggest value for least effort / dependency first.** You can
  reorder, but later phases often assume earlier ones.
- Each item is tagged:
  - **[AGENT]** — I can build it autonomously (no money, no live decision, no keys).
  - **[FRED]** — needs you: an API key, money, an account, or a yes/no decision.
  - **[BOTH]** — I build it; you supply a key/credential to switch it on.
- **Effort** is rough dev time once unblocked (S = hours, M = 1–2 days, L = 3–5 days).
- "Already in code" means the plumbing exists and is dormant — switching it on is
  small, not a rebuild.

## Where we are right now (the baseline)
**LIVE** at https://web-production-9c290.up.railway.app — Railway + Supabase, admin
login works, `web` + `worker` online, AI on (GPT-5.5).

**Working today:** client management; The Radar engine (Profile → research → grounded
plan → write → 8-point quality gate → schedule → post → refresh); no-key feeds
(holidays/events calendar, Google Trends best-effort, Google News, competitor website
scrape); AI images (Plus tier); per-client autopilot UI (toggle, cadence, run-now,
connect platform, Zapier connect, test/disconnect).

**Simulated or dormant today (the gap this roadmap closes):**
1. **Posting is simulated** — posts are marked "posted (SIMULATED)" unless a real
   connector is attached. Real posting code exists for FB/IG/X/LinkedIn/TikTok +
   Zapier; it needs credentials.
2. **Radar feeds dormant:** reviews (Yelp/Google Places) and local events
   (Ticketmaster/TMDB) are stubs that return nothing; deeper market data not built;
   robust scraping of blocked sites needs a scraping API.
3. **No approval/review step** — generated posts go straight to scheduled/posted;
   there's no "salesperson approves before it goes live."
4. **Analytics is placeholder** — it counts campaigns and shows static "vs. agency"
   figures; no real engagement/impressions pulled back from platforms.
5. **No learning loop** — the system doesn't yet learn each client's winning patterns.
6. **Notifications are log-only** — no real email/SMS alerts to the salesperson.
7. **Media is ephemeral** — generated images live in a temp folder, wiped on redeploy
   (the Railway volume didn't attach; object storage is the right fix).
8. **Scale tooling is thin** — fine for a handful of clients; running 100 needs bulk
   views, per-client cadence config, and guided onboarding.
9. **Tech debt** — leftover B2C/pricing language, inconsistent "Brand"→"Client"
   relabel, admin metrics that count internal accounts, an unfinished licensing
   feature, OpenAI key that should be rotated.

---

## Phase summary (at a glance)

| Phase | Theme | Headline outcome | Main dependency |
|---|---|---|---|
| 0 | Launch hardening | Safe, durable, observable in prod | Mostly [AGENT]; key rotation [FRED] |
| 1 | **Real posting** | Posts actually publish to clients' accounts | Zapier (free) or social dev apps [FRED] |
| 2 | Approval + alerts | Salesperson reviews before it goes live; gets notified | Email provider key [FRED] |
| 3 | Expand the Radar | Reviews + local events + market data feeds live | Yelp/Places/Ticketmaster keys [FRED] |
| 4 | Real analytics + learning | True performance data → system learns winners | Built on Phase 1 posting |
| 5 | Scale to 100 clients | Bulk ops, cadence config, guided onboarding | [AGENT] |
| 6 | Video (Pro tier) | AI video posts for Pro clients | Video provider key + $ [FRED] |
| 7 | Polish + tech debt | Clean internal-tool UX, correct metrics | [AGENT] |

---

## Phase 0 — Launch hardening (do first; mostly me, fast)
*Goal: make the live app safe, durable, and debuggable before you put real clients on it.*

0.1 **Rotate the OpenAI key** — **[FRED+AGENT]** — S. Your current key passed through
chat. You make a new one at platform.openai.com; I swap it on Railway via the CLI in
seconds and delete the old one.

0.2 **Persistent media storage (replace the failed volume)** — **[AGENT]** — M.
The Railway volume wouldn't attach, and object storage is the better answer anyway.
Steps: (a) create a Supabase **Storage** bucket (free tier) in your Dominate Supabase;
(b) add `SUPABASE_URL` + `SUPABASE_SERVICE_KEY` env vars; (c) change image save/serve
code to upload to the bucket and return its public URL; (d) update `PUBLIC_BASE_URL`
usage so posted images have durable links. *Result: generated images survive redeploys
and are postable.* (You provide the two Supabase values; I wire the code.)

0.3 **Error monitoring** — **[AGENT]** — S. Add Sentry (free tier) so crashes/500s are
captured with stack traces instead of vanishing into logs. You make a free Sentry
project → give me the DSN → I wire it.

0.4 **AI cost guardrails** — **[AGENT]** — S/M. You watch costs, so: per-day spend cap
+ per-client generation cap (config via env), a hard stop when exceeded, and a small
"AI spend this month" readout on the admin dashboard. Prevents a runaway loop from
burning money.

0.5 **Daily database backup** — **[FRED]** — S. Confirm Supabase's automatic backups
are on for your project (free tier has limited retention; the paid tier adds
point-in-time). Decision only: accept free-tier backups now, upgrade later.

0.6 **Custom domain (optional)** — **[FRED]** — S. If you want it on
`dominatemarketing.ninja` (already referenced in config) instead of the railway.app URL:
add the domain in Railway → set the DNS CNAME → update `PUBLIC_BASE_URL` and the Google
OAuth callback. I do the app side; you click the DNS.

---

## Phase 1 — Real posting (THE core value unlock)
*Goal: the autopilot actually publishes to clients' real social accounts. Today it
simulates. The code is built for both routes below — this is configuration + UI, not a
rebuild.*

**Decision first — pick the route (you can do both):**

### Route A — Zapier per client (fastest, recommended to start) — **[BOTH]** — M
No app-store review, works for any platform Zapier supports, code already supports it
(`_post_via_webhook`). Per client:
1. In Zapier, create a Zap: trigger **"Catch Hook"** (Webhooks by Zapier) → action
   **"Create Post"** on the client's Facebook Page / Instagram / LinkedIn / X.
2. Copy the Catch Hook URL.
3. In the app: client page → autopilot → **"Connect via Zapier"** → paste the URL.
4. The autopilot now POSTs each scheduled post to that Zap, which publishes it.
- **What I build:** harden the webhook payload (include image URL, scheduled time,
  per-platform formatting), a "send test post" button (exists — verify end to end),
  and clear per-platform status. **What you provide:** a Zapier account (free tier
  works for low volume; paid for scale) and 5 min of setup per client.
- **Cost:** Zapier free = limited tasks/month; ~$20–50/mo unlocks real volume.

### Route B — Native social apps (more reach, more setup) — **[BOTH]** — L
Direct API posting (no Zapier middleman, no per-task cost), code already exists
(`_post_to_facebook/instagram/twitter/linkedin/tiktok` + OAuth in
`social_auth_service.py`). Per platform (not per client):
1. Create a developer app: Meta (covers FB + Instagram), X/Twitter, LinkedIn, TikTok.
2. Get client_id + client_secret; set `FACEBOOK_CLIENT_ID/SECRET`, `TWITTER_*`,
   `LINKEDIN_*`, `TIKTOK_*` on Railway.
3. Set the OAuth callback to your domain (`/social/callback/<platform>`).
4. **Submit each app for review** (Meta/TikTok/X require app review to post on behalf
   of users — this takes days–weeks and is the real gating item).
5. Clients then click **"Connect Facebook"** etc. on their client page (flow exists).
- **What I build:** finish/verify the OAuth connect screens, token refresh, and
  per-platform error handling. **What you provide:** the dev apps + the review process.
- **Reality check:** start with Route A (Zapier) to get live posting now; pursue Route
  B for platforms/clients where the per-task cost or polish matters.

### 1.1 Freshness-clock verification — **[AGENT]** — S
Confirm/enforce that the Strategist only uses signals inside the recency window before a
post publishes (the BLUEPRINT promises this; verify it's enforced at post time, not just
at research time), and surface each post's "built from data dated X" stamp in the UI.

---

## Phase 2 — Approval workflow + real notifications
*Goal: the "human + learning loop" (BLUEPRINT layer 6) — a salesperson reviews/edits
before anything goes live, and gets told when something needs attention. Critical once
posting is real.*

2.1 **Approval pipeline** — **[AGENT]** — M. Add a post status `pending_review` between
"generated" and "scheduled." New screen: a per-client (and all-clients) **review queue**
where the salesperson can **approve / edit / regenerate / reject** each post, see the
image, the copy, the quality score, and the source signals it's grounded in. Autopilot
mode toggle: "auto-post" vs "hold for approval" per client.

2.2 **Real notifications** — **[BOTH]** — S/M. `admin_notifications.py` currently only
logs. Wire a real email provider (SendGrid or Amazon SES free tier). Alerts: "N posts
awaiting your approval," "a post failed to publish," "a client's website became
unreadable," "weekly summary per client." **You provide:** the email provider key.
Optional later: SMS via Twilio.

2.3 **Per-post edit history & audit** — **[AGENT]** — S. Keep who-approved-what and the
original-vs-edited copy, so quality is traceable across 100 clients.

---

## Phase 3 — Expand the Radar (the real moat)
*Goal: turn on the dormant feeds. BLUEPRINT says the product lives or dies on the
Radar's data, not the AI. Add feeds one at a time, highest-signal first.*

3.1 **Reviews feed (Yelp + Google Places)** — **[BOTH]** — M. `fetch_reviews()` is a
dormant stub. Wire **Yelp Fusion API** (free tier) and/or **Google Places API** to pull
the client's and competitors' recent reviews → feed the Strategist (e.g., "competitor
slammed for slow service → post about your fast turnaround"). **You provide:** Yelp
Fusion key (free) and/or Google Places key (paid per call, has free credit).

3.2 **Local events feed (Ticketmaster + TMDB)** — **[BOTH]** — M. `fetch_local_events()`
is a dormant stub. Wire **Ticketmaster Discovery API** (concerts/sports, free tier) and
**TMDB** (movie releases, free) keyed to the client's city → "big game Saturday → game-day
promo." **You provide:** Ticketmaster + TMDB keys (both free).

3.3 **Deeper market/economic signals** — **[AGENT/BOTH]** — M. Add lightweight market
signals (weather for weather-driven businesses via a free weather API; simple economic
indicators) that the BLUEPRINT calls out (heat wave vs blackout selling different lamps).
Start with a free weather API. **You provide:** a weather API key (free tier).

3.4 **Scraping API for blocked sites** — **[BOTH]** — M. `scrape_website()` notes a
dormant connector. Many sites block the headless browser. Add a scraping-API fallback
(e.g., Bright Data / ScraperAPI / ScrapingBee) so competitor/client profiles work on
sites that currently fail. **You provide:** a scraping-API key (paid; pick a budget
tier). *Note: I have Bright Data tooling available and can prototype this.*

3.5 **Feed health dashboard** — **[AGENT]** — S. A per-client view of which feeds are
live, last-refreshed timestamps, and which are dormant (so you can see the moat working
and know what a key would unlock).

---

## Phase 4 — Real analytics + the learning loop
*Goal: replace placeholder analytics with true performance data, then close the loop so
the system learns each client's winners. Depends on Phase 1 (real posting) to have real
numbers.*

4.1 **Real performance metrics** — **[BOTH]** — M/L. Pull engagement/impressions/clicks
back from platforms (via the same APIs from Route B, or via Zapier return paths / manual
import for Route A) into `SocialPost` metrics. Replace the placeholder `/analytics`
(currently campaign counts + static agency-comparison) with real per-post, per-client,
per-platform dashboards.

4.2 **Winning-pattern learning** — **[AGENT]** — L. Analyze which themes/formats/timing
win per client and bias the Strategist toward them (BLUEPRINT layer 6: "the system learns
each client's winning patterns"). Start rules-based (best day/time, best-performing
themes), evolve toward a per-client scoring model.

4.3 **Client-facing report** — **[AGENT]** — M. A shareable monthly report per client
("here's what we posted, here's what it drove, here's what's next") — a sales/retention
asset that also reinforces the "better than the agency" story.

---

## Phase 5 — Scale to 100 clients per salesperson
*Goal: make the BLUEPRINT endgame operationally real. Today's UI is fine for a handful;
100 needs bulk tooling.*

5.1 **All-clients command center** — **[AGENT]** — M. One screen across all clients:
autopilot status, posts pending approval, feed health, failures, next refresh — sortable,
filterable, with bulk actions (approve all, pause, run-now).

5.2 **Per-client cadence & strategy config UI** — **[AGENT]** — M. Surface per-client
settings (posts/week, platforms, tone, recency window, auto vs review) in the UI rather
than defaults/code.

5.3 **Guided client onboarding** — **[AGENT]** — M. A wizard: enter website → auto-build
Profile → confirm/adjust → connect accounts (Zapier/OAuth) → pick cadence → go. Turns
"add a client" into a 5-minute repeatable flow.

5.4 **Queue/prioritization + rate-limit safety** — **[AGENT]** — M. Make the worker
fair across 100 clients (don't starve any), with backoff against AI and platform rate
limits, and cost-aware batching.

---

## Phase 6 — Video (Pro / Enterprise tier)
*Goal: AI video posts for higher tiers. Clients (`veo_client.py`, `pika_labs_service.py`,
`google_veo_service.py`) exist but are dormant.*

6.1 **Wire a video provider** — **[BOTH]** — M. Pick Veo / Pika / Sora, set
`VIDEO_PROVIDER_API_KEY`, enable generation in the Studio for Pro+ clients, pass through
the quality gate, store via Phase 0.2 object storage. **You provide:** the provider key +
budget (video is the most expensive generation).

6.2 **Video posting** — **[AGENT]** — S. Ensure the posting connectors handle video
assets (FB/IG/TikTok especially) for the platforms you target.

---

## Phase 7 — Polish & tech debt (clean internal-tool UX)
*Goal: finish the B2C→internal pivot and fix the known sharp edges. Low risk, all me.*

7.1 **Remove leftover B2C/pricing language** — **[AGENT]** — S. Templates still say
"Upgrade your plan" / "Subscription Tier" in places despite billing being off.

7.2 **Finish "Brand"→"Client" relabel** — **[AGENT]** — S. Make it consistent across all
screens (DB stays "brand" under the hood).

7.3 **Fix admin metrics** — **[AGENT]** — S. Exclude internal accounts
(`is_salesperson`/`is_admin`) from customer-count/MRR reports (TODO'd in `admin.py`) so
numbers aren't inflated.

7.4 **Licensing feature: fix or remove** — **[FRED decision + AGENT]** — S/M. The
`/licensing/*` feature errors on bad input and isn't linked anywhere. Decide: remove it,
or fix it if you want media licensing.

7.5 **Per-tier client limit honors billing_disabled()** — **[AGENT]** — S. Low-risk
correctness fix in `create_brand`.

7.6 **Public marketing pages decision** — **[FRED decision]** — S. For an internal tool:
keep the landing/features/faq pages, simplify them, or route straight to login.

---

## What I need from you to unblock each phase (the shopping list)

| Need | Unlocks | Cost |
|---|---|---|
| New OpenAI key | 0.1 | free to make |
| Supabase Storage values | 0.2 persistent images | free tier |
| Sentry DSN | 0.3 monitoring | free tier |
| Zapier account | 1A real posting (fast) | free→$20–50/mo |
| Meta/X/LinkedIn/TikTok dev apps + review | 1B native posting | free, but review takes weeks |
| Email provider key (SendGrid/SES) | 2.2 notifications | free tier |
| Yelp Fusion / Google Places key | 3.1 reviews feed | free / paid-with-credit |
| Ticketmaster + TMDB keys | 3.2 events feed | free |
| Weather API key | 3.3 market signals | free tier |
| Scraping API key | 3.4 blocked sites | paid (pick budget) |
| Video provider key | 6.1 video | paid (highest) |

## Recommended order if you just want "what next"
1. **Phase 0.1 + 0.2** (rotate key, persistent images) — quick, I do most of it.
2. **Phase 1 Route A** (Zapier posting) — this is the moment it stops being a demo.
3. **Phase 2.1** (approval queue) — so you trust it with real client accounts.
4. **Phase 3.1 + 3.2** (reviews + events feeds) — the moat the BLUEPRINT is built on.
5. Then analytics/learning (4), scale (5), video (6), polish (7) as the book of
   business grows.

*Every [AGENT] item I can build now without spending your money or going further live.
Every [FRED]/[BOTH] item is blocked only on a key, a dollar, or a decision — tell me
which and I'll wire it the moment it's in hand.*
