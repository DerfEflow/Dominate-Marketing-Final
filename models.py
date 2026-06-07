import os
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, timedelta
from enum import Enum
import uuid

db = SQLAlchemy()


def billing_disabled():
    """True when the SaaS billing layer is turned off (internal-tool mode).

    Toggle by setting DISABLE_BILLING=true in Railway env. When this is true,
    paywalls, tier gates, and Stripe checkout flows are bypassed for everyone
    so the app behaves like a free internal tool. Stripe code stays registered
    but the entry points redirect away. Flip back to false (or unset) to
    re-enable the SaaS path for a future D2C launch.
    """
    return os.environ.get('DISABLE_BILLING', '').lower() in ('1', 'true', 'yes', 'on')


class SubscriptionTier(Enum):
    BASIC = "basic"          # Text ads only + posting recommendations
    PLUS = "plus"            # + Image generation & download
    PRO = "pro"              # + Video/audio generation + competitor analysis + editing
    ENTERPRISE = "enterprise" # + Automated social media posting

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    # email is now nullable so admin-created salesperson accounts (which sign in
    # with username + password and never see Google OAuth) can omit it. The
    # unique index still applies when email is present.
    email = db.Column(db.String(120), unique=True, nullable=True, index=True)
    username = db.Column(db.String(80), unique=True, nullable=False)

    # ---- Internal-tool roles (added 2026-05-09 with the B2C → internal pivot) ----
    # METRICS FOOTGUN: any future revenue / MRR / SaaS-funnel reporting query
    # MUST filter `is_salesperson=False` AND `is_admin=False` to avoid mixing
    # internal accounts into customer counts before the eventual D2C relaunch.
    # See admin.py monthly_registrations / tier_distribution for examples that
    # currently need this filter applied.
    is_salesperson = db.Column(db.Boolean, default=False, nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    created_by_admin_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)

    # OAuth provider info
    google_id = db.Column(db.String(100), unique=True)
    twitter_id = db.Column(db.String(100), unique=True)

    # Password auth
    password_hash = db.Column(db.String(255))
    
    # Profile info
    full_name = db.Column(db.String(200))
    avatar_url = db.Column(db.String(500))
    company_name = db.Column(db.String(200))
    industry = db.Column(db.String(100))
    
    # Marketing capture data
    phone_number = db.Column(db.String(20))
    job_title = db.Column(db.String(100))
    company_size = db.Column(db.String(50))  # "1-10", "11-50", "51-200", "201-500", "500+"
    annual_revenue = db.Column(db.String(50))  # Revenue ranges for targeting
    marketing_budget = db.Column(db.String(50))  # Monthly marketing spend
    primary_marketing_channels = db.Column(db.Text)  # JSON array of channels
    marketing_goals = db.Column(db.Text)  # Text description of goals
    target_audience = db.Column(db.Text)  # Description of target customers
    biggest_marketing_challenge = db.Column(db.Text)  # Pain points
    how_heard_about_us = db.Column(db.String(100))  # Traffic source tracking
    
    # Communication preferences
    email_marketing_consent = db.Column(db.Boolean, default=False)
    sms_marketing_consent = db.Column(db.Boolean, default=False)
    newsletter_subscription = db.Column(db.Boolean, default=True)
    product_updates_consent = db.Column(db.Boolean, default=True)
    
    # Geographic data
    country = db.Column(db.String(100))
    state_province = db.Column(db.String(100))
    city = db.Column(db.String(100))
    timezone = db.Column(db.String(50))
    
    # Profile completion tracking
    profile_completion_percentage = db.Column(db.Integer, default=20)  # Start at 20% for basic signup
    onboarding_completed = db.Column(db.Boolean, default=False)
    
    # Subscription info
    subscription_tier = db.Column(db.Enum(SubscriptionTier), default=SubscriptionTier.BASIC)
    subscription_expires = db.Column(db.DateTime)
    stripe_customer_id = db.Column(db.String(100), unique=True)
    stripe_subscription_id = db.Column(db.String(100), unique=True)
    
    # Coupon system
    coupon_used = db.Column(db.String(100))  # Track which coupon was used
    trial_expires = db.Column(db.DateTime)   # For 24-hour trials
    lifetime_access = db.Column(db.Boolean, default=False)  # For lifetime coupons
    
    # Generation tracking
    generations_used_this_month = db.Column(db.Integer, default=0)
    generations_used_today = db.Column(db.Integer, default=0)
    last_generation_date = db.Column(db.Date)
    billing_period_start = db.Column(db.DateTime)
    
    # Account hold system
    account_on_hold = db.Column(db.Boolean, default=False)
    hold_start_date = db.Column(db.DateTime)
    hold_end_date = db.Column(db.DateTime)
    last_hold_year = db.Column(db.Integer)
    
    # Payment failure tracking
    payment_failed_date = db.Column(db.DateTime)
    account_deletion_date = db.Column(db.DateTime)
    
    # Account status
    account_active = db.Column(db.Boolean, default=True)
    is_demo_account = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Custom business info document
    business_document_path = db.Column(db.String(500))
    
    # Relationships
    brands = db.relationship('Brand', backref='user', lazy=True, cascade='all, delete-orphan')
    campaigns = db.relationship('Campaign', backref='user', lazy=True, cascade='all, delete-orphan')
    social_accounts = db.relationship('SocialAccount', backref='user', lazy=True, cascade='all, delete-orphan')
    competitors = db.relationship('Competitor', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def has_active_subscription(self):
        # Internal-tool short-circuit: salespeople and admins don't pay; when
        # billing is globally disabled, treat everyone as subscribed. Keeps the
        # SaaS code paths intact for the eventual D2C relaunch.
        if self.is_salesperson or self.is_admin or billing_disabled():
            return True

        # Check for lifetime access first
        if self.lifetime_access:
            return True

        # Check for active trial
        if self.trial_expires and datetime.utcnow() < self.trial_expires:
            return True

        # Check regular subscription
        if not self.subscription_expires:
            return False
        return datetime.utcnow() < self.subscription_expires

    def can_access_tier(self, required_tier):
        # Internal accounts and billing-disabled mode always pass. This lets
        # every existing template gate (`{% if can_access_tier('pro') %}`) and
        # service-side tier check keep working without modification — they just
        # silently return True for salespeople/admins.
        if self.is_salesperson or self.is_admin or billing_disabled():
            return True

        if not self.has_active_subscription():
            return required_tier == SubscriptionTier.BASIC

        tier_order = [SubscriptionTier.BASIC, SubscriptionTier.PLUS, SubscriptionTier.PRO, SubscriptionTier.ENTERPRISE]
        return tier_order.index(self.subscription_tier) >= tier_order.index(required_tier)

    @property
    def generations_used(self):
        """Back-compat alias used by some templates/code paths."""
        return self.generations_used_this_month or 0

    def get_tier_config(self):
        """Return the feature/limit config for this user's tier.

        Internal users (salespeople/admins) and billing-disabled mode get
        effectively unlimited generations so tier gates never block them.
        """
        cfg = dict(TIER_CONFIGS.get(self.subscription_tier, TIER_CONFIGS[SubscriptionTier.BASIC]))
        if self.is_salesperson or self.is_admin or billing_disabled():
            cfg = dict(cfg)
            cfg['generations_per_month'] = UNLIMITED
            cfg['generations_per_day'] = UNLIMITED
        return _TierConfig(cfg)


UNLIMITED = 999999


class _TierConfig:
    """Lightweight attribute view over a tier-config dict (templates use dots)."""
    def __init__(self, data):
        self._data = data
    def __getattr__(self, name):
        try:
            return self._data[name]
        except KeyError as e:
            raise AttributeError(name) from e


TIER_CONFIGS = {
    SubscriptionTier.BASIC: {
        'name': 'Basic', 'price_monthly': 29, 'generations_per_month': 30,
        'generations_per_day': 3, 'ai_models': 'GPT-4o',
        'features': ['Text ads', 'Posting recommendations'],
    },
    SubscriptionTier.PLUS: {
        'name': 'Plus', 'price_monthly': 59, 'generations_per_month': 100,
        'generations_per_day': 10, 'ai_models': 'GPT-4o + image generation',
        'features': ['Everything in Basic', 'Image generation & download'],
    },
    SubscriptionTier.PRO: {
        'name': 'Pro', 'price_monthly': 99, 'generations_per_month': 300,
        'generations_per_day': 30, 'ai_models': 'GPT-4o + Claude + video',
        'features': ['Everything in Plus', 'Video/audio', 'Competitor analysis'],
    },
    SubscriptionTier.ENTERPRISE: {
        'name': 'Enterprise', 'price_monthly': 199, 'generations_per_month': UNLIMITED,
        'generations_per_day': UNLIMITED, 'ai_models': 'All models',
        'features': ['Everything in Pro', 'Automated social posting'],
    },
}


class Brand(db.Model):
    __tablename__ = 'brands'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    
    # Brand information
    name = db.Column(db.String(200), nullable=False)
    website_url = db.Column(db.String(500))
    industry = db.Column(db.String(100))
    description = db.Column(db.Text)
    logo_url = db.Column(db.String(500))

    # ---- Client-management fields (added 2026-05-09 with the internal pivot) ----
    # Brand still represents an entity owning campaigns, but for internal-tool
    # mode it's relabeled "Client" in the UI. These columns capture the contact
    # info a salesperson needs to manage their book of business.
    contact_name = db.Column(db.String(200))
    contact_email = db.Column(db.String(200))
    contact_phone = db.Column(db.String(40))
    billing_notes = db.Column(db.Text)
    monthly_retainer = db.Column(db.Numeric(10, 2))
    status = db.Column(db.String(20), default='active', nullable=False)  # active|paused|onboarding|churned
    onboarded_at = db.Column(db.DateTime)
    notes = db.Column(db.Text)

    # ---- Automation engine (added 2026-06-07) ----
    # Per-client autopilot: when enabled, the scheduler periodically refreshes
    # this client's research, generates fresh content, and schedules posts.
    automation_enabled = db.Column(db.Boolean, default=False, nullable=False)
    posting_frequency_days = db.Column(db.Integer, default=3, nullable=False)
    last_research_at = db.Column(db.DateTime)        # freshness of source data
    research_snapshot = db.Column(db.Text)           # latest research as JSON

    # Subscription info (per brand billing)
    subscription_tier = db.Column(db.Enum(SubscriptionTier), default=SubscriptionTier.BASIC)
    subscription_expires = db.Column(db.DateTime)
    stripe_subscription_id = db.Column(db.String(100), unique=True)
    
    # Brand status
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    campaigns = db.relationship('Campaign', backref='brand', lazy=True, cascade='all, delete-orphan')
    social_accounts = db.relationship('SocialAccount', backref='brand', lazy=True, cascade='all, delete-orphan')
    competitors = db.relationship('Competitor', backref='brand', lazy=True, cascade='all, delete-orphan')
    
    def has_active_subscription(self):
        if not self.subscription_expires:
            return False
        return datetime.utcnow() < self.subscription_expires
    
    def can_access_tier(self, required_tier):
        if not self.has_active_subscription():
            return required_tier == SubscriptionTier.BASIC
        
        tier_order = [SubscriptionTier.BASIC, SubscriptionTier.PLUS, SubscriptionTier.PRO, SubscriptionTier.ENTERPRISE]
        return tier_order.index(self.subscription_tier) >= tier_order.index(required_tier)

class SocialAccount(db.Model):
    __tablename__ = 'social_accounts'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    brand_id = db.Column(db.String(36), db.ForeignKey('brands.id'), nullable=True)  # Optional brand association
    
    platform = db.Column(db.String(50), nullable=False)  # 'twitter', 'facebook', 'instagram', 'linkedin'
    platform_user_id = db.Column(db.String(100))
    username = db.Column(db.String(100))
    access_token = db.Column(db.Text)
    refresh_token = db.Column(db.Text)
    # Simulated connection (demo / no real OAuth app yet). Posts to a simulated
    # account are marked posted with a SIMULATED marker instead of a real API call.
    is_simulated = db.Column(db.Boolean, default=False, nullable=False)
    # Zapier (or any) webhook URL. When set, posts are sent here (a Zapier
    # "Catch Hook") which posts to the client's real account — no platform
    # developer app needed. Takes precedence over direct-API / simulated posting.
    webhook_url = db.Column(db.Text)
    token_expires = db.Column(db.DateTime)
    
    # Auto-posting settings
    auto_post_enabled = db.Column(db.Boolean, default=False)
    post_frequency_hours = db.Column(db.Integer, default=24)  # How often to post
    vary_content = db.Column(db.Boolean, default=True)  # Generate new content each time
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Campaign(db.Model):
    __tablename__ = 'campaigns'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    brand_id = db.Column(db.String(36), db.ForeignKey('brands.id'), nullable=True)  # Optional brand association
    
    # Basic campaign info
    title = db.Column(db.String(200))
    business_url = db.Column(db.String(500))
    target_audience = db.Column(db.String(200))
    campaign_goal = db.Column(db.String(100))
    brand_voice = db.Column(db.String(100))
    
    # Marketing Strategy Analysis fields
    campaign_type = db.Column(db.String(50), default='general')  # 'strategy_analysis', 'content_generation', etc.
    target_url = db.Column(db.String(500))  # For website analysis campaigns
    analysis_data = db.Column(db.Text)  # JSON data for analysis results
    confidence_score = db.Column(db.Float, default=0.0)
    
    # Scraped business data
    business_metadata = db.Column(db.JSON)  # Scraped website data
    keywords = db.Column(db.JSON)  # Extracted keywords
    differentiators = db.Column(db.JSON)  # What makes them unique
    
    # AI-generated content
    marketing_theme = db.Column(db.Text)
    ad_text = db.Column(db.Text)
    image_prompt = db.Column(db.Text)
    video_prompt = db.Column(db.JSON)  # Advanced AI video JSON prompt
    
    # Generated media paths
    image_path = db.Column(db.String(500))
    video_path = db.Column(db.String(500))
    
    # Campaign status and AI integration
    status = db.Column(db.String(50), default='draft')  # draft, processing, completed, failed
    ai_content = db.Column(db.Text)  # Store AI-generated content as JSON
    quality_score = db.Column(db.Integer, default=0)  # Quality assessment score
    tier_used = db.Column(db.String(20))  # Subscription tier when created
    services_used = db.Column(db.Text)  # JSON array of AI services used
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    # Auto-posting settings
    auto_post_enabled = db.Column(db.Boolean, default=False)
    next_post_time = db.Column(db.DateTime)
    
    # Relationships
    posts = db.relationship('SocialPost', backref='campaign', lazy=True, cascade='all, delete-orphan')


class StrategyAnalysis(db.Model):
    __tablename__ = 'strategy_analyses'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    campaign_id = db.Column(db.String(36), db.ForeignKey('campaigns.id'), nullable=False)
    brand_id = db.Column(db.String(36), db.ForeignKey('brands.id'), nullable=False)
    
    # Analysis Target Information
    target_url = db.Column(db.String(500), nullable=False)
    geo_location = db.Column(db.String(10), default='US')
    confidence_score = db.Column(db.Float, default=0.0)
    data_sources = db.Column(db.Text)  # JSON array of data sources used
    
    # Analysis Data (JSON fields)
    business_intelligence = db.Column(db.Text)  # JSON: business info, services, contact
    competitor_analysis = db.Column(db.Text)    # JSON: competitor data and insights
    trend_analysis = db.Column(db.Text)         # JSON: trend data and patterns
    content_opportunities = db.Column(db.Text)  # JSON: content suggestions and calendar
    
    # Technical Analysis Metadata
    scraping_successful = db.Column(db.Boolean, default=False)
    fallback_protocols_used = db.Column(db.Boolean, default=False)
    metadata_extracted = db.Column(db.Boolean, default=False)
    
    # Update and Version Control
    update_history = db.Column(db.Text)  # JSON: history of confidence updates
    analysis_timestamp = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    campaign = db.relationship('Campaign', backref=db.backref('strategy_analyses', lazy=True))
    brand = db.relationship('Brand', backref=db.backref('strategy_analyses', lazy=True))

class Competitor(db.Model):
    __tablename__ = 'competitors'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    brand_id = db.Column(db.String(36), db.ForeignKey('brands.id'), nullable=True)  # Optional brand association
    
    company_name = db.Column(db.String(200), nullable=False)
    website_url = db.Column(db.String(500))
    description = db.Column(db.Text)
    
    # Competitive analysis
    strengths = db.Column(db.JSON)
    weaknesses = db.Column(db.JSON)
    ad_strategies = db.Column(db.JSON)  # Their successful ad approaches
    
    # AI-detected or user-added
    is_ai_detected = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class SocialPost(db.Model):
    __tablename__ = 'social_posts'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    campaign_id = db.Column(db.String(36), db.ForeignKey('campaigns.id'), nullable=False)
    
    platform = db.Column(db.String(50), nullable=False)  # facebook, instagram, twitter, tiktok, linkedin
    platform_post_id = db.Column(db.String(200))  # ID from the social platform
    
    content = db.Column(db.Text)
    scheduled_for = db.Column(db.DateTime)
    post_frequency = db.Column(db.String(20), default='once')  # once, daily, weekly, monthly
    
    # Status tracking
    status = db.Column(db.String(20), default='scheduled')  # scheduled, posted, failed, cancelled
    posted_at = db.Column(db.DateTime)
    error_message = db.Column(db.Text)
    
    # Auto-posting settings
    is_recurring = db.Column(db.Boolean, default=False)
    next_post_time = db.Column(db.DateTime)
    image_url = db.Column(db.String(500))
    video_url = db.Column(db.String(500))
    
    # Post metrics
    likes = db.Column(db.Integer, default=0)
    shares = db.Column(db.Integer, default=0)
    comments = db.Column(db.Integer, default=0)
    reach = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class QualityCheck(db.Model):
    __tablename__ = 'quality_checks'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    campaign_id = db.Column(db.String(36), db.ForeignKey('campaigns.id'), nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    
    # Quality assessment results
    check_results = db.Column(db.JSON)  # Full quality assessment data
    passed = db.Column(db.Boolean, nullable=False)
    quality_score = db.Column(db.Numeric(4, 2))  # Overall quality score 0-10
    regeneration_attempt = db.Column(db.Integer, default=1)
    
    # Quality criteria scores
    coherent_score = db.Column(db.Numeric(3, 1))
    relevant_score = db.Column(db.Numeric(3, 1))
    compelling_score = db.Column(db.Numeric(3, 1))
    fresh_score = db.Column(db.Numeric(3, 1))
    unique_score = db.Column(db.Numeric(3, 1))
    creative_score = db.Column(db.Numeric(3, 1))
    edgy_score = db.Column(db.Numeric(3, 1))
    worth_paying_score = db.Column(db.Numeric(3, 1))
    
    # Failure analysis
    failed_criteria = db.Column(db.JSON)  # List of criteria that failed
    specific_issues = db.Column(db.JSON)  # Detailed issues found
    improvement_recommendations = db.Column(db.JSON)  # Recommendations for improvement
    
    # Processing metadata
    model_used = db.Column(db.String(50), default='gpt-5-mini')
    processing_time_ms = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    campaign = db.relationship('Campaign', backref='quality_checks')
    user = db.relationship('User', backref='quality_checks')