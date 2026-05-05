# Dominate Marketing — Deployment Guide
## Stack: GitHub → Railway (Flask app + worker) + Supabase (PostgreSQL)

---

## Step 1 — Push to GitHub

Create a fresh repo on GitHub (suggested name: `dominate-marketing`), then:

```bash
cd domiMarket_fixed
git init
git add .
git commit -m "Initial production build"
git remote add origin https://github.com/DerfEflow/dominate-marketing.git
git push -u origin main
```

The `.gitignore` is properly configured — no `.pyc` files, databases, or secrets will be included.

---

## Step 2 — Set Up Supabase (Database)

1. Go to [supabase.com](https://supabase.com) → New Project
2. Choose a region close to your users (US East is a safe default)
3. Once the project is ready: **Project Settings → Database → Connection String → URI**
4. Copy the URI — it looks like:
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-REF].supabase.co:5432/postgres
   ```
5. Save this — it becomes your `DATABASE_URL` environment variable
6. **No manual migrations needed** — the app creates all tables automatically on first boot

---

## Step 3 — Deploy Web App on Railway

1. Go to [railway.app](https://railway.app) → **New Project → Deploy from GitHub repo**
2. Connect your GitHub account and select the `dominate-marketing` repo
3. Railway will auto-detect `railway.toml` and handle the build (installs deps + Playwright Chromium)
4. Once deployed, Railway gives you a domain like `your-app.up.railway.app`

### Add Environment Variables (Railway Dashboard → Variables tab)

| Variable | Where to get it | Required? |
|---|---|---|
| `SESSION_SECRET` | Generate any 40+ char random string | ✅ Yes |
| `DATABASE_URL` | Supabase connection string (Step 2) | ✅ Yes |
| `OPENAI_API_KEY` | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) | ✅ Yes |
| `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com) | ✅ Yes |
| `GOOGLE_API_KEY` | [console.cloud.google.com](https://console.cloud.google.com) | ✅ Yes (Veo 3 + Vision) |
| `GOOGLE_OAUTH_CLIENT_ID` | Google Cloud Console → Credentials | ✅ Yes (login) |
| `GOOGLE_OAUTH_CLIENT_SECRET` | Google Cloud Console → Credentials | ✅ Yes (login) |
| `STRIPE_SECRET_KEY` | [dashboard.stripe.com/apikeys](https://dashboard.stripe.com/apikeys) | ✅ Yes (payments) |
| `STRIPE_PUBLISHABLE_KEY` | Stripe Dashboard | ✅ Yes (payments) |
| `STRIPE_WEBHOOK_SECRET` | Stripe Dashboard → Webhooks | ✅ Yes (payments) |
| `STRIPE_PRICE_BASIC` | Stripe Dashboard → Products | ✅ Yes (payments) |
| `STRIPE_PRICE_PLUS` | Stripe Dashboard → Products | ✅ Yes (payments) |
| `STRIPE_PRICE_PRO` | Stripe Dashboard → Products | ✅ Yes (payments) |
| `STRIPE_PRICE_ENTERPRISE` | Stripe Dashboard → Products | ✅ Yes (payments) |
| `ADMIN_EMAIL` | Your email (fredwolfe@gmail.com) | ✅ Yes |
| `SERPAPI_KEY` | [serpapi.com](https://serpapi.com) | Optional |
| `GOOGLE_CUSTOM_SEARCH_CX` | Google Cloud Console | Optional |

---

## Step 4 — Add the Social Scheduler Worker

The background scheduler that auto-posts to social media runs as a **separate service** on Railway.

1. In your Railway project, click **+ New Service → Empty Service**
2. Connect it to the same GitHub repo
3. In the service settings, set the **Start Command** to:
   ```
   python services/social_scheduler.py
   ```
4. Add the same environment variables as the web service
5. Deploy — this worker runs independently and checks for due posts every 60 seconds

---

## Step 5 — Update Google OAuth Callback URL

Once Railway gives you your live domain:

1. Go to [console.cloud.google.com/apis/credentials](https://console.cloud.google.com/apis/credentials)
2. Edit your OAuth 2.0 Client ID
3. Under **Authorized redirect URIs**, add:
   ```
   https://your-app.up.railway.app/auth/google_login/callback
   ```
   (Replace `your-app` with your actual Railway subdomain)
4. Also add your custom domain here if you connect one later

---

## Step 6 — Set Up Stripe Webhooks

1. Go to [dashboard.stripe.com/webhooks](https://dashboard.stripe.com/webhooks) → **Add endpoint**
2. Endpoint URL:
   ```
   https://your-app.up.railway.app/payments/webhook
   ```
3. Select these events to listen for:
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
4. Copy the **Signing secret** → set as `STRIPE_WEBHOOK_SECRET` in Railway

---

## Step 7 — Create Stripe Products

In Stripe Dashboard → **Products → Add product** for each tier:

| Tier | Price | Suggested name |
|---|---|---|
| Basic | $29/month | Dominate Basic |
| Plus | $59/month | Dominate Plus |
| Pro | $99/month | Dominate Pro |
| Enterprise | $199/month | Dominate Enterprise |

After creating each, copy the **Price ID** (starts with `price_`) and set the corresponding Railway variable.

---

## Coupon Codes (Already Built In)

These coupon codes are hardcoded in `auth.py` and work immediately:

| Code | Effect |
|---|---|
| `SAINTSDOMINION` | 24-hour free trial of Enterprise |
| `SAINTSDOMINIONSTEWARD` | Lifetime Enterprise access |

---

## Custom Domain (Optional)

1. Railway → your web service → **Settings → Domains → Add Custom Domain**
2. Add a CNAME record at your DNS provider pointing to the Railway domain
3. Update the Google OAuth callback URL to use your custom domain

---

## Architecture Overview

```
GitHub repo
    │
    ├── Railway Web Service (gunicorn, 2 workers, 4 threads)
    │     main_app.py → Flask app → 88 routes
    │     Connects to Supabase PostgreSQL
    │
    └── Railway Worker Service (background thread)
          services/social_scheduler.py
          Checks for due social posts every 60 seconds

Supabase
    └── PostgreSQL database (users, brands, campaigns, social_posts, etc.)

External APIs
    ├── OpenAI (GPT-4o text generation + DALL-E 3 images)
    ├── Anthropic Claude (quality assessment agent)
    ├── Google AI (Veo 3 video generation)
    ├── Stripe (subscriptions + payments)
    └── Social platforms (Facebook, Instagram, Twitter, LinkedIn)
```

---

## Troubleshooting

**App won't start:** Check Railway logs. Most likely a missing environment variable — `SESSION_SECRET` and `DATABASE_URL` are required for any page to load.

**Database tables missing:** They're created automatically on boot. If they're not there, check that `DATABASE_URL` is set correctly and the Supabase project is active.

**Google login not working:** The OAuth callback URL in Google Cloud Console must exactly match your Railway domain including `https://`.

**Stripe webhooks failing:** Make sure `STRIPE_WEBHOOK_SECRET` is set to the webhook signing secret (starts with `whsec_`), not the API key.

**Playwright / screenshot scraper not working:** Railway's build command installs Chromium automatically via `python -m playwright install chromium --with-deps`. If it fails, check the build logs for system dependency errors.

---

*Built with Flask, SQLAlchemy, OpenAI, Anthropic Claude, Google Veo 3, Stripe, Playwright*
*Deployed on Railway + Supabase*
