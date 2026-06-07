"""
Automation Engine — the per-client autopilot.

run_cycle(brand) does the full loop:
  1. refresh_source_data  → fresh research snapshot (trends/competitors/profile)
  2. generate_posts       → AI turns research + brand voice into ready posts
  3. schedule_posts       → spread posts across the client's connected platforms

Every external dependency degrades gracefully so the whole engine runs end to
end with NO API keys or social connectors (simulation mode). When real keys /
connectors are present, the same functions use them instead.

See docs/automation_engine.md for the design.
"""

import os
import json
import logging
from datetime import datetime, timedelta

from models import db, Brand, Campaign, SocialAccount, SocialPost

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Configuration detection (simulation vs real)
# ---------------------------------------------------------------------------
def ai_configured():
    """True if any AI provider key is set and simulation isn't forced on."""
    if os.environ.get('AI_SIMULATE', '').lower() in ('1', 'true', 'yes', 'on'):
        return False
    return any(os.environ.get(k) for k in ('OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'GOOGLE_API_KEY'))


def social_configured(platform):
    """True if OAuth app credentials exist for a platform (so real connect works)."""
    if os.environ.get('SOCIAL_SIMULATE', '').lower() in ('1', 'true', 'yes', 'on'):
        return False
    prefix = {'instagram': 'FACEBOOK'}.get(platform, platform.upper())
    return bool(os.environ.get(f'{prefix}_CLIENT_ID') and os.environ.get(f'{prefix}_CLIENT_SECRET'))


# ---------------------------------------------------------------------------
# 1. Research / fresh source data
# ---------------------------------------------------------------------------
def refresh_source_data(brand):
    """Build (and persist) a fresh research snapshot for a client.

    Real path uses the website/competitor/trend research services; if AI isn't
    configured or any step fails, a deterministic on-topic placeholder snapshot
    is built so the pipeline still flows and is reviewable.
    """
    snapshot = None
    if ai_configured() and brand.website_url:
        try:
            snapshot = _real_research(brand)
        except Exception as e:
            logger.warning(f"Real research failed for {brand.name}, using placeholder: {e}")
    if snapshot is None:
        snapshot = _placeholder_research(brand)

    snapshot['generated_at'] = datetime.utcnow().isoformat()
    snapshot['mode'] = 'live' if ai_configured() else 'simulated'
    brand.research_snapshot = json.dumps(snapshot)
    brand.last_research_at = datetime.utcnow()
    db.session.commit()
    return snapshot


def _real_research(brand):
    from services.sell_profile_analyzer import SellProfileAnalyzer
    from services.viral_tools_researcher import ViralToolsResearcher
    analyzer = SellProfileAnalyzer()
    profile = analyzer.export_profile(analyzer.analyze_website(brand.website_url))
    researcher = ViralToolsResearcher()
    viral = researcher.export_research(researcher.research_viral_tools(profile))
    return {
        'profile': profile,
        'trends': viral.get('trending_topics') or viral.get('viral_tools') or [],
        'keywords': profile.get('keywords', []),
        'summary': f"Live research for {brand.name}: "
                   f"{len(profile.get('keywords', []))} keywords, "
                   f"{len(viral.get('viral_tools', []))} viral angles.",
    }


def _placeholder_research(brand):
    """Deterministic, industry-aware placeholder research (no AI needed)."""
    industry = (brand.industry or 'business').lower()
    seeds = {
        'real estate': ['home staging tips', 'first-time buyer guides', 'local market updates', 'virtual tours'],
        'healthcare': ['preventive care', 'patient wellness', 'telehealth tips', 'seasonal health'],
        'technology': ['AI in the workplace', 'automation wins', 'cybersecurity basics', 'product how-tos'],
        'food & beverage': ['seasonal menu', 'behind the kitchen', 'local sourcing', 'customer favorites'],
        'fitness': ['quick workouts', 'nutrition myths', 'progress stories', 'recovery tips'],
        'professional services': ['client success stories', 'industry insights', 'how-we-help explainers', 'FAQs'],
    }
    trends = seeds.get(industry, ['behind the scenes', 'customer spotlights', 'tips & how-tos', 'seasonal promotions'])
    return {
        'profile': {
            'business_name': brand.name,
            'industry': brand.industry or 'General',
            'about': brand.description or f'{brand.name} serves its local market.',
        },
        'trends': [{'topic': t, 'momentum': 'rising'} for t in trends],
        'keywords': trends,
        'summary': f"Simulated research for {brand.name} ({brand.industry or 'general'}): "
                   f"{len(trends)} on-trend content angles identified.",
    }


# ---------------------------------------------------------------------------
# 2. Content generation
# ---------------------------------------------------------------------------
def generate_posts(brand, count=4):
    """Return a list of ready-to-schedule posts derived from the research snapshot.

    Real path uses the AI ContentGenerator; otherwise templated, on-topic posts
    built from the research snapshot + brand voice.
    """
    snapshot = json.loads(brand.research_snapshot) if brand.research_snapshot else _placeholder_research(brand)

    if ai_configured():
        try:
            return _real_posts(brand, snapshot, count)
        except Exception as e:
            logger.warning(f"AI content generation failed for {brand.name}, using templates: {e}")
    return _templated_posts(brand, snapshot, count)


def _real_posts(brand, snapshot, count):
    from services.content_generator import ContentGenerator
    gen = ContentGenerator()
    viral = {'viral_tools': snapshot.get('trends', [])}
    content = gen.generate_campaign_content(snapshot.get('profile', {}), viral, tier='pro')
    posts = []
    for item in (content.get('texts') or content.get('content') or [])[:count]:
        text = item.get('content') if isinstance(item, dict) else str(item)
        posts.append({'content': text, 'simulated': False})
    return posts or _templated_posts(brand, snapshot, count)


def _templated_posts(brand, snapshot, count):
    """On-topic templated posts (no AI). Varied so a batch doesn't repeat."""
    name = brand.name
    trends = [t['topic'] if isinstance(t, dict) else str(t) for t in snapshot.get('trends', [])]
    if not trends:
        trends = ['our latest work', 'a customer favorite', 'tips from our team', 'what makes us different']
    templates = [
        "📣 {topic}: here's how {name} can help. Reach out today!",
        "Did you know? {name} specializes in {topic}. Ask us how.",
        "This week at {name}: {topic}. DM us to learn more 👇",
        "{topic} is trending — and {name} has you covered. Let's talk.",
        "Behind the scenes at {name}: {topic}. We love what we do!",
        "Tip of the day from {name}: {topic}. Save this post 📌",
    ]
    posts = []
    for i in range(count):
        topic = trends[i % len(trends)]
        tmpl = templates[i % len(templates)]
        posts.append({'content': tmpl.format(topic=topic, name=name), 'simulated': True})
    return posts


# ---------------------------------------------------------------------------
# 3. Scheduling
# ---------------------------------------------------------------------------
def _automation_campaign(brand):
    """Find or create the campaign that automation-scheduled posts attach to."""
    camp = Campaign.query.filter_by(brand_id=brand.id, campaign_type='automation').first()
    if not camp:
        import uuid
        camp = Campaign(
            id=str(uuid.uuid4()), user_id=brand.user_id, brand_id=brand.id,
            title=f"Automation — {brand.name}", campaign_type='automation',
            status='active', campaign_goal='engagement',
        )
        db.session.add(camp)
        db.session.commit()
    return camp


def schedule_posts(brand, posts, first_delay_minutes=1):
    """Create SocialPost rows for each of the client's connected platforms.

    First post is scheduled `first_delay_minutes` out (so a demo "process due
    posts" publishes one immediately); subsequent posts are spaced by the
    client's posting cadence.
    """
    accounts = SocialAccount.query.filter_by(brand_id=brand.id, is_active=True).all()
    if not accounts:
        return {'scheduled': 0, 'reason': 'no connected accounts for this client'}

    camp = _automation_campaign(brand)
    cadence = max(1, brand.posting_frequency_days or 3)
    base = datetime.utcnow() + timedelta(minutes=first_delay_minutes)
    created = 0
    for idx, post in enumerate(posts):
        when = base + timedelta(days=cadence * idx)
        for acct in accounts:
            sp = SocialPost(
                user_id=brand.user_id,
                campaign_id=camp.id,
                platform=acct.platform,
                content=post['content'],
                scheduled_for=when,
                status='scheduled',
            )
            db.session.add(sp)
            created += 1
    db.session.commit()
    return {'scheduled': created, 'platforms': [a.platform for a in accounts]}


# ---------------------------------------------------------------------------
# Full cycle
# ---------------------------------------------------------------------------
def run_cycle(brand, post_count=4):
    """The autopilot tick for one client: refresh → generate → schedule."""
    snapshot = refresh_source_data(brand)
    posts = generate_posts(brand, count=post_count)
    sched = schedule_posts(brand, posts)
    summary = {
        'client': brand.name,
        'mode': snapshot.get('mode'),
        'research_summary': snapshot.get('summary'),
        'posts_generated': len(posts),
        'posts_scheduled': sched.get('scheduled', 0),
        'note': sched.get('reason'),
        'ran_at': datetime.utcnow().isoformat(),
    }
    logger.info(f"Automation cycle for {brand.name}: {summary}")
    return summary


def due_for_refresh(brand):
    """True if an automation-enabled client's research is older than its cadence."""
    if not brand.automation_enabled:
        return False
    if not brand.last_research_at:
        return True
    age_days = (datetime.utcnow() - brand.last_research_at).total_seconds() / 86400
    return age_days >= max(1, brand.posting_frequency_days or 3)


def run_due_clients():
    """Run the cycle for every automation-enabled client whose data is stale.

    Called by the scheduler worker — this is the 'continual fresh source data'
    driver.
    """
    ran = []
    for brand in Brand.query.filter_by(automation_enabled=True).all():
        if due_for_refresh(brand):
            try:
                ran.append(run_cycle(brand))
            except Exception as e:
                logger.error(f"Automation cycle failed for {brand.name}: {e}")
    return ran
