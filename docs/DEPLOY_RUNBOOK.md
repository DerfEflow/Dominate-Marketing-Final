# Deploy Runbook (Railway + Supabase) — beginner steps

Going live needs YOUR accounts and a card on file (Railway + Supabase have free
tiers but can incur usage charges, and AI/image calls cost money). I can't do
these for you, but each step is spelled out, and I can do the code-side parts and
sit with you for the rest. Do them in order.

Legend: **[YOU]** = only you can do it · **[I CAN]** = I'll do it for you on request.

---

## Step 1 — Get the code onto GitHub  [I CAN, with your OK]
The app is committed locally on the `autonomous-pivot` branch. Railway deploys
from GitHub. I can merge it into `main` and push to your repo
(github.com/DerfEflow/Dominate-Marketing-Final). Just say "push it."

## Step 2 — Create the database (Supabase)  [YOU]
1. Go to supabase.com → New project (pick a name, a strong DB password, a region).
2. Wait for it to finish provisioning.
3. Project Settings → Database → Connection string → **URI**. Copy it.
   It looks like `postgresql://postgres:[PASSWORD]@db.xxxx.supabase.co:5432/postgres`.
   That's your **DATABASE_URL**. (Use a **fresh, empty** project — see Step 5 note.)

## Step 3 — Create the Railway project  [YOU]
1. Go to railway.app → New Project → Deploy from GitHub repo → pick the repo.
2. Railway reads `railway.toml`/`Procfile` automatically (build installs the
   browser for screenshots; start runs the web server).

## Step 4 — Set environment variables in Railway  [YOU] (I'll give exact values)
In the Railway project → Variables, add these. The must-haves to boot + run AI:

| Variable | Value |
|---|---|
| `SESSION_SECRET` | any long random string (I can generate one) |
| `DATABASE_URL` | the Supabase URI from Step 2 |
| `DISABLE_BILLING` | `true` (internal-tool mode) |
| `FLASK_ENV` | `production` |
| `OPENAI_API_KEY` | your OpenAI key |
| `OPENAI_TEXT_MODEL` | `gpt-5.5` (primary — auto-falls back to gpt-4o-mini; see note) |
| `OPENAI_TEXT_MODEL_FALLBACK` | *(optional)* — backup model; defaults to `gpt-4o-mini` |
| `OPENAI_IMAGE_MODEL` | *(optional)* — defaults to `gpt-image-1-mini` |
| `BOOTSTRAP_ADMIN_USERNAME` | your admin login name |
| `BOOTSTRAP_ADMIN_PASSWORD` | a strong password (this is your real login) |
| `BOOTSTRAP_ADMIN_EMAIL` | fredwolfe@gmail.com |
| `ADMIN_EMAIL` | fredwolfe@gmail.com |

(Leave Stripe/Google-OAuth/social-connector vars blank for now — dormant.)

> **Model note:** every text/vision generation calls `OPENAI_TEXT_MODEL`
> (`gpt-5.5`) first and **automatically retries on `OPENAI_TEXT_MODEL_FALLBACK`
> (`gpt-4o-mini`) if the primary errors** — e.g. if your OpenAI account can't yet
> call gpt-5.5. So gpt-5.5 is used whenever it's available, and content
> generation never breaks if it isn't (it downshifts to 4o-mini and logs a
> warning, instead of dropping to placeholder/simulated output). The fallback is
> overridable via `OPENAI_TEXT_MODEL_FALLBACK`.

## Step 5 — First deploy  [YOU click, automatic after]
Trigger the deploy. On release, the app automatically runs
`flask db upgrade` (builds the whole database schema from the migration files)
then `flask bootstrap-admin` (creates your admin login).
- **Fresh empty Supabase DB → do NOT run `flask db stamp`.** Just let it deploy;
  the migrations create everything. (The "stamp first" note in MIGRATIONS.md is
  ONLY for a database that already has the tables.)

## Step 6 — Point the app at its own address  [YOU] (I'll confirm)
After the first deploy, Railway gives you a URL like
`https://your-app.up.railway.app`. Add one more variable:
- `PUBLIC_BASE_URL` = that URL
Then redeploy. (This lets generated images post with a public link.)

## Step 7 — Turn on the 24/7 autopilot worker  [YOU]
In Railway, add a second service/process for the **worker** line in the Procfile
(`python services/social_scheduler.py`). This is what makes the engine refresh
research and post on schedule around the clock. (The web service alone serves
pages; the worker runs the automation.)

## Step 8 — Make images persist  [YOU]
Containers are wiped on each redeploy, so add a Railway **Volume** mounted at
`/app/static/uploads`. That keeps generated images (and lets them stay
publicly reachable for posting).

## Step 9 — Log in and verify  [YOU + I CAN review]
Open your Railway URL, log in with the admin username/password from Step 4,
open a client, and run the autopilot. Tell me and I'll review the live site.

---

## After launch (optional, each needs its own key)
- Social OAuth apps or Zapier zaps → real posting to clients' accounts.
- Yelp/Maps + events API keys → switch on the dormant Radar feeds.
- A video provider key → Pro-tier video.
- A scraping API → guaranteed reading of sites that block the browser render.
