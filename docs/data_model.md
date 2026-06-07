# Data model

Defined in `models.py` (SQLAlchemy). Schema is owned by Flask-Migrate
(`migrations/versions/`) — see `MIGRATIONS.md`. Never `db.create_all()`.

## User (`users`)
The account. Login is by **email + password** (see auth.py), or Google OAuth.
- Pivot fields: `is_salesperson`, `is_admin`, `created_by_admin_id`.
- `email` is **nullable** (so admin-created salespeople could use username-only).
  NOTE: the current login form only accepts email — see ROADMAP item about
  salesperson login.
- SaaS fields (dormant in internal mode): `subscription_tier` (enum
  BASIC/PLUS/PRO/ENTERPRISE), `subscription_expires`, Stripe ids, coupon/trial,
  generation counters, account-hold fields.
- `has_active_subscription()` / `can_access_tier()` short-circuit to **True** for
  salespeople, admins, or when `billing_disabled()` — so tier gates pass for
  internal staff without changing every template.

## Brand (`brands`) — "Client" in the internal UI
An entity that owns campaigns. Belongs to a User.
- Core: `name`, `website_url`, `industry`, `description`, `logo_url`.
- Pivot/client-mgmt fields: `contact_name`, `contact_email`, `contact_phone`,
  `billing_notes`, `monthly_retainer`, `status` (active/paused/onboarding/churned),
  `onboarded_at`, `notes`.

## Campaign (`campaigns`)
A marketing campaign. Belongs to a User; `brand_id` is **nullable** (a campaign
can exist without a client attached).
- Inputs: `title`, `business_url`/`target_url`, `target_audience`,
  `campaign_goal`, `brand_voice`, `campaign_type`.
- Generated content: `marketing_theme`, `ad_text`, `image_prompt`,
  `video_prompt`, `ai_content` (JSON), media paths.
- Status/meta: `status` (draft/pending/processing/completed/failed),
  `tier_used`, `services_used` (JSON — also reused to store content-type choices),
  `quality_score`.
  NOTE: there is **no** `content_preferences` column (a prior bug referenced one).

## Other tables
- `StrategyAnalysis` — website-analysis results per campaign/brand.
- `Competitor` — AI-detected or user-added competitors.
- `SocialAccount` — connected social platforms + auto-post settings.
- `SocialPost` — scheduled/posted social content + metrics.
- `QualityCheck` — AI content QA scores per campaign.

## Metrics footgun (documented in models.py)
Any future SaaS/MRR/customer-count reporting must filter
`is_salesperson == False AND is_admin == False`, or internal accounts inflate
customer numbers. Several admin reports still need this filter (TODO'd in admin.py).
