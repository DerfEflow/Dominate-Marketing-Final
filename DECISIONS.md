# Decisions log (plain English)

Every judgment call made while working autonomously, newest at the bottom of
each section. This is so Fred can review *choices* without reading code.

## Platform (locked — not changed)
- The app is set up for **Railway** (hosting) + **Supabase Postgres** (database),
  with **SQLite** as the automatic local-dev database and **Flask-Migrate** for
  schema changes. I confirmed this from the config files and kept it exactly.

## Setup choices
- **Worked on a branch** called `autonomous-pivot` (off `main`), committing
  often, so `main` stays a known-good fallback and any change can be undone.
- **Local database = SQLite**, built from the migration files (not by guessing
  the schema). The old leftover local DB had no migration stamp, so I deleted
  that throwaway file and rebuilt it cleanly. (Only the *local* dev DB — nothing
  to do with any real/production data.)
- **Local login for review:** put throwaway admin credentials in the local-only
  `.env` (never committed): log in with the email **fredwolfe@gmail.com** and
  password **localdev123**. Change these before any real launch.
- **Turned on internal-tool mode locally** (`DISABLE_BILLING=true`) so the review
  experience matches the pivot (no pricing/subscription screens).
- **Ran the app on port 5055 locally**, because port 5000 (and 5001) were already
  taken by other apps you had running. Several leftover "zombie" Python servers
  from other projects were occupying ports; I only stopped *this app's* own
  leftover processes, never the other projects'.

## Fixes (what I changed and why)
- **Made the app boot without any API keys.** Several background modules used to
  create AI/Trends clients (or even make a network call) the instant the app
  started, which crashed it when keys/packages were missing. I made those create
  themselves only when actually used. The app now starts fully offline with all
  paid features dormant. (selenium, Google Trends, Google Cloud Vision/Language.)
- **Fixed ~9 pages that errored (500).** Each was a page asking the template for
  data the page code forgot to provide (admin dashboard, quality control,
  analytics, social scheduling, AI status, campaign status, etc.). I supplied the
  missing data. Also created one missing page template (admin Quality Control).
- **Fixed a database query** that only worked on the production database type
  (Postgres) and crashed on the local one (SQLite); rewrote it to work on both.
- **Repaired campaign creation.** Both campaign forms pointed at buttons/links
  that didn't exist, and the code tried to save a field the database doesn't
  have. I added the missing create-campaign pages, removed the bad field, and
  made one shared, reliable "create a campaign" path. A campaign can now be
  created with or without a client attached; if AI isn't configured it just says
  so instead of erroring.
- **Fixed salesperson login (important pivot fix).** Salespeople are created with
  a username (email optional), but the login screen only accepted an email — so a
  salesperson literally couldn't sign in. Login now accepts **email or username**.

## Pivot polish (Phase 2 — finishing the internal tool)
- **Made client management real.** The database already had fields for a
  client's contact name/email/phone, monthly retainer, status, and notes, but
  no screen actually collected them. Added an "Add Client" / "Edit Client" form
  that captures all of it, and the client page now shows a tidy contact card.
  This is the heart of what a salesperson needs.
- **Renamed "Brand" to "Client"** in the menu and main screens (the database
  still calls it "brand" under the hood — that's invisible to you and avoids
  risky code changes).
- **Removed the leftover sales/pricing bits** (plan badges, "Upgrade",
  subscription status) from the staff-facing screens, since this is an internal
  tool with billing turned off.
- **One client page, not two.** There were two different client detail pages;
  I kept the better one and pointed everything at it.
- **Added a sample client** ("Summit Roofing Co") with a campaign so the app
  isn't empty when you first open it. You can edit or delete it.
- **Left the public marketing pages and the unused "licensing" feature alone**
  for now — they don't affect the salesperson experience (noted in ROADMAP).

## The Automation Engine (the autopilot)
- **Built the core "set it and forget it" loop**: for each client the system
  refreshes market research, generates fresh on-trend posts, schedules them,
  and auto-posts to the client's connected social accounts — then keeps
  refreshing on a cadence so content never goes stale.
- **It all runs and is reviewable right now WITHOUT any keys or social logins**,
  in "simulation" mode: research uses sensible placeholder data, content is
  generated from templates, accounts can be "connected (simulated)," and posts
  are marked posted with a SIMULATED tag instead of going to a real network. The
  instant you add real keys and connect real accounts, the exact same buttons do
  the real thing — no rebuild.
- **Decided accounts/automation live on the *client*, not the salesperson**,
  because each client has their own pages and audience. You connect a client's
  accounts and flip on autopilot from that client's screen.
- **Reused the existing code** (the real Facebook/Instagram/X/LinkedIn posting
  code and OAuth flow already existed but were disconnected and unused) — I wired
  them together and added the missing "keep refreshing" loop and the on/off UI.
- **Why simulation matters for you**: you can see the whole engine work and judge
  whether it's what you want *before* spending on AI usage or setting up social
  apps. Reduces risk and makes it demoable to your salespeople immediately.
- To see it: open a client → "Marketing Autopilot" panel → connect a platform or
  two (simulated) → "Run now" → watch posts get scheduled, then auto-posted.

## The rebuild: grounded engine ("The Radar")
- **Rethought the whole content engine around your vision** (see docs/BLUEPRINT.md):
  the AI is no longer allowed to invent posts. It may only turn **real, fresh
  research into content** — so a small business out-markets the big competitor.
- **What it now does each cycle:** (1) builds a **Client Profile** by scraping the
  client's real website; (2) gathers **real signals** — upcoming holidays/events
  (real calendar), rising Google Trends, the client's own site news, and
  competitor sites if listed; (3) writes a **plan grounded only in those real
  signals**; (4) writes each post and runs it through an 8-point quality check;
  (5) schedules + posts. Everything is time-stamped so it's never built on stale data.
- **Honest limit I hit:** reliably scraping *any* website is hard — many big sites
  block automated reading. I improved our scraper (real browser identity + it now
  rejects blocked/error pages instead of writing junk), but truly robust scraping
  at scale will need a paid scraping service later (noted as a future connector).
  When a site can't be read, it still works — grounded in the real calendar +
  trends + the info you provided.
- **Demo client** switched to "Bright Ideas Lighting" using a real, readable
  lighting-store website, so you can see genuine grounding (it pulled the store's
  actual Spring sale and real rising lighting trends). Add a roofing client
  anytime; if its site blocks reading, it falls back gracefully.
- **Still on the roadmap (your vision, next):** images (Plus tier) and video
  (Pro), and more Radar feeds (Yelp/Maps reviews, news/sports/movies) — each
  needs an API key/connector, so they're built to plug in.

## Screenshots + AI vision (your Google Vision question)
- You asked about Google Vision; I recommended and built a better fit: the system
  now **opens each client's website in a real browser, takes a screenshot, and has
  GPT‑5.5 *look at it*** — using the OpenAI key you already have (no Google Cloud
  account needed). It understands design, products, vibe and brand colors, not just
  text. Bonus: rendering the page in a browser also **gets past many sites that
  block plain reading**, so the profile is richer and works on more sites.
- The client page now shows a **"What our AI learned"** card with the screenshot
  and the facts it extracted. (Google Vision stays a possible later add-on for
  exact logo/colors when we build image generation.)
- One gotcha handled: GPT‑5.5 spends part of its budget "thinking," so the vision
  request needed more room or it returned blank — fixed.

## Images, more feeds, video (built while you were away)
- **Images (Plus tier):** posts now get a **real AI-generated image** (using your
  OpenAI key). Generated, saved, and shown as thumbnails on the client page.
  Used the cheaper image model by default (gpt-image-1-mini) since you watch costs.
  Note: to actually *post* an image (vs. preview it), the app needs to be live on
  the web so the image has a public address — a launch step. Today images
  generate + preview locally.
- **More research feeds:** added a **real, free news feed** (Google News
  headlines for the client's topics — no key needed), wired into the Radar.
  Yelp/Google-Maps reviews and live sports/movie/concert events are built as
  ready-to-activate slots that switch on when you add those API keys.
- **Video (Pro tier):** the slot is built and wired, but real AI video needs a
  paid video provider key (Veo/Pika/Sora), so it stays off until you add one.
- **Tiers wired:** Basic = text only; Plus = + images; Pro = + video. (The demo
  client is set to Pro so you can see images.)
- **Tuning:** GPT‑5.5 grades its own writing harshly, so I lowered the
  auto-rewrite bar to avoid needless (paid) regenerations.

## Secret hygiene
- The committed `.env.example` contains only placeholders (good). The real local
  `.env` is git-ignored and was never committed.
- I did a quick check and did **not** find a real API key committed in the code.
  Before launch, still treat any key that has ever been pasted anywhere as worth
  rotating, just to be safe.

## Things left for Fred (see ROADMAP Phase 4 — these are the "hard blocks")
- Real secrets, real admin login, real API keys, the live Supabase database, and
  the actual deploy. I did not touch any of these — they cost money, go live, or
  need your private accounts.
