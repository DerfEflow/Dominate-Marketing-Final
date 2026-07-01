"""
Automation Engine — the grounded marketing pipeline (per client).

The core rule (see docs/BLUEPRINT.md): the AI never invents content from thin
air. It only SYNTHESIZES real, fresh research into creative output.

run_cycle(brand):
  1. ensure_profile   → Foundational Client Profile (DNA) from a website scrape
  2. gather_radar     → fresh, time-stamped signals (trends/events/competitor/news)
  3. build_plan       → AI marketing plan grounded ONLY in those signals + profile
  4. studio           → write each post + 8-criteria quality gate (regenerate weak)
  5. schedule_posts   → spread across the client's connected platforms

Everything degrades gracefully with no AI key (templated) and no connectors
(simulated posting), so it's reviewable end to end. With keys/connectors it runs
for real. Freshness is enforced: signals are time-stamped and re-gathered each cycle.
"""

import os
import json
import uuid
import logging
from datetime import datetime, timedelta

from models import db, Brand, Campaign, SocialAccount, SocialPost, Competitor
from services import radar

logger = logging.getLogger(__name__)

PROFILE_MAX_AGE_DAYS = 30   # re-scrape the client profile at least this often


# ---------------------------------------------------------------------------
# Config detection (live vs simulated)
# ---------------------------------------------------------------------------
def ai_configured():
    if os.environ.get('AI_SIMULATE', '').lower() in ('1', 'true', 'yes', 'on'):
        return False
    return any(os.environ.get(k) for k in ('OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'GOOGLE_API_KEY'))


def social_configured(platform):
    if os.environ.get('SOCIAL_SIMULATE', '').lower() in ('1', 'true', 'yes', 'on'):
        return False
    prefix = {'instagram': 'FACEBOOK'}.get(platform, platform.upper())
    return bool(os.environ.get(f'{prefix}_CLIENT_ID') and os.environ.get(f'{prefix}_CLIENT_SECRET'))


def text_model():
    # Primary text/vision model for every generation call. Per the product spec
    # (docs/BLUEPRINT.md) this is GPT-5.5. _openai_chat / _openai_vision call
    # this model first and AUTOMATICALLY retry on fallback_text_model() if it
    # errors (e.g. the OpenAI account can't call this id yet), so an
    # unavailable primary never breaks generation — it just downshifts.
    return os.environ.get('OPENAI_TEXT_MODEL', 'gpt-5.5')


def fallback_text_model():
    # Backup model used only when the primary (text_model) call fails. gpt-4o-mini
    # is broadly available and cheap, so it's a safe always-works net.
    return os.environ.get('OPENAI_TEXT_MODEL_FALLBACK', 'gpt-4o-mini')


def _chat_completion(client, **kwargs):
    """chat.completions.create on the primary model, with one automatic retry on
    the fallback model if the primary errors. Returns the response object.

    Also guards the GPT-5.x reasoning-starvation trap: if the model spends the
    whole token budget reasoning and returns EMPTY content (finish_reason
    'length'), retry once with a much larger budget. That empty-return silently
    degraded plans/profiles to the generic template."""
    primary = text_model()
    fallback = fallback_text_model()
    try:
        resp = client.chat.completions.create(model=primary, **kwargs)
    except Exception as e:
        if fallback and fallback != primary:
            logger.warning("Primary model %s failed (%s) — retrying on fallback %s",
                           primary, e, fallback)
            return client.chat.completions.create(model=fallback, **kwargs)
        raise
    try:
        choice = resp.choices[0]
        empty = not (choice.message.content or '').strip()
        starved = getattr(choice, 'finish_reason', '') == 'length'
        budget = kwargs.get('max_completion_tokens')
        if empty and starved and budget:
            kwargs['max_completion_tokens'] = budget * 3
            logger.info("Empty response at %s tokens (reasoning starvation) — retrying at %s",
                        budget, kwargs['max_completion_tokens'])
            return client.chat.completions.create(model=primary, **kwargs)
    except Exception:
        pass
    return resp


def image_model():
    # mini is the cost-sensible default for batch social images.
    return os.environ.get('OPENAI_IMAGE_MODEL', 'gpt-image-1-mini')


# Tier gating: images on Plus+, video on Pro+ (see docs/BLUEPRINT.md).
_TIER_RANK = {'basic': 0, 'plus': 1, 'pro': 2, 'enterprise': 3}


def _tier_rank(brand):
    return _TIER_RANK.get(getattr(brand.subscription_tier, 'value', 'basic'), 0)


def wants_images(brand):
    return ai_configured() and _tier_rank(brand) >= 1


def wants_video(brand):
    return _tier_rank(brand) >= 2


# ---------------------------------------------------------------------------
# OpenAI helpers (GPT-5.x compatible: max_completion_tokens, default temperature)
# ---------------------------------------------------------------------------
def _openai_chat(system, prompt, max_tokens=1500):
    from openai import OpenAI
    client = OpenAI()
    resp = _chat_completion(
        client,
        messages=[{'role': 'system', 'content': system},
                  {'role': 'user', 'content': prompt}],
        max_completion_tokens=max_tokens,
    )
    return (resp.choices[0].message.content or '').strip()


def _openai_vision(image_bytes, prompt, max_tokens=400):
    """Send an image to the (vision-capable) model for interpretation.

    GPT-5.x / GPT-4o accept images. Returns text, or '' on failure.
    """
    import base64
    from openai import OpenAI
    client = OpenAI()
    data_url = 'data:image/png;base64,' + base64.b64encode(image_bytes).decode()
    resp = _chat_completion(
        client,
        max_completion_tokens=max_tokens,
        messages=[{'role': 'user', 'content': [
            {'type': 'text', 'text': prompt},
            {'type': 'image_url', 'image_url': {'url': data_url}},
        ]}],
    )
    return (resp.choices[0].message.content or '').strip()


def _openai_image(prompt, size='1024x1024'):
    """Generate an image and return PNG bytes (or None). Uses the OpenAI key."""
    import base64
    from openai import OpenAI
    client = OpenAI()
    r = client.images.generate(model=image_model(), prompt=prompt, size=size, n=1)
    d = r.data[0]
    if getattr(d, 'b64_json', None):
        return base64.b64decode(d.b64_json)
    if getattr(d, 'url', None):
        import requests
        return requests.get(d.url, timeout=30).content
    return None


def _save_post_media(brand, data, kind='img', ext='png'):
    """Persist generated post media and return a URL/path usable for posting.

    Prefers durable PUBLIC hosting (Supabase Storage) so the image can be fetched
    by social platforms/Zapier and survives redeploys; returns a full public URL.
    Falls back to local static/uploads (fine for local dev; ephemeral on Railway).
    """
    if not data:
        return None
    # Durable public hosting first.
    try:
        from services import storage
        if storage.is_configured():
            ct = {'png': 'image/png', 'jpg': 'image/jpeg', 'jpeg': 'image/jpeg',
                  'mp4': 'video/mp4'}.get(ext, 'application/octet-stream')
            url = storage.upload_bytes(data, ext=ext, content_type=ct,
                                       prefix=f"{kind}/{brand.id}")
            if url:
                return url
    except Exception as e:
        logger.info(f"supabase media upload skipped: {e}")
    # Local fallback.
    try:
        folder = os.path.join('static', 'uploads')
        os.makedirs(folder, exist_ok=True)
        fname = f"{kind}_{brand.id}_{uuid.uuid4().hex[:8]}.{ext}"
        with open(os.path.join(folder, fname), 'wb') as f:
            f.write(data)
        return f"uploads/{fname}"
    except Exception as e:
        logger.info(f"could not save post media: {e}")
        return None


def _image_prompt(brand, profile, brief, caption):
    colors = ', '.join(profile.get('brand_colors', [])[:3]) if profile.get('brand_colors') else ''
    return (f"Professional social media image for {brand.name}, a business that sells "
            f"{profile.get('what_they_sell')}. Theme: {brief.get('angle')}. "
            f"Clean, modern, scroll-stopping, architectural/product photography. "
            f"{('Brand colors: ' + colors + '. ') if colors else ''}"
            # HARD RULE (Fred): never depict a person applying ROOF COATING specifically —
            # AI renders those tools/technique wrong. Traditional roofing work IS fine.
            f"ABSOLUTE RULE: do NOT depict any person applying or performing roof COATING "
            f"(liquid/spray/roller-applied roof coating) — those specific tools and techniques "
            f"render incorrectly. Traditional roofing work is acceptable, but never show "
            f"someone applying a roof coating. Prefer the building, the roof, the finished "
            f"clean result, or clean brand imagery. "
            f"Do NOT include any text, words, or logos in the image.")


def _strip_fences(text):
    text = text.strip()
    if text.startswith('```'):
        text = text.strip('`')
        text = text[text.find('\n') + 1:] if '\n' in text else text
    return text.strip()


def _parse_json(text, default):
    try:
        return json.loads(_strip_fences(text))
    except Exception:
        return default


def _parse_list(text):
    data = _parse_json(text, None)
    if isinstance(data, list):
        return [str(x).strip() for x in data if str(x).strip()]
    out = []
    for ln in text.splitlines():
        ln = ln.strip().lstrip('-*0123456789. ').strip().strip('"')
        if ln:
            out.append(ln)
    return out


# ---------------------------------------------------------------------------
# 1. Foundational Client Profile (the DNA)
# ---------------------------------------------------------------------------
def _profile_stale(brand):
    if not brand.client_profile or not brand.profile_built_at:
        return True
    return (datetime.utcnow() - brand.profile_built_at) > timedelta(days=PROFILE_MAX_AGE_DAYS)


# Fields the salesperson can hand-edit on the client page. (key, label, kind).
# `list` fields accept newline- or comma-separated input. Edits are stored as
# overrides and merged on top of the AI-built profile so a re-scrape never wipes them.
EDITABLE_PROFILE_FIELDS = [
    ('what_they_sell', 'What they sell', 'text'),
    ('service_area', 'Service area', 'text'),
    ('service_area_cities', 'Cities / regions served', 'list'),
    ('offers', 'Offers / services', 'list'),
    ('target_audience', 'Target audience', 'text'),
    ('voice', 'Brand voice', 'text'),
    ('tone', 'Tone (adjectives)', 'text'),
    ('proof_points', 'Proof points', 'list'),
    ('differentiators', 'Differentiators', 'list'),
    ('brand_colors', 'Brand colors', 'list'),
    ('banned_topics', 'Banned topics (never post about)', 'list'),
    ('keywords', 'Search keywords', 'list'),
]
_EDITABLE_KEYS = {k for k, _, _ in EDITABLE_PROFILE_FIELDS}


def _load_overrides(brand):
    if not getattr(brand, 'profile_overrides', None):
        return {}
    try:
        data = json.loads(brand.profile_overrides)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _apply_overrides(profile, overrides):
    """Human edits win over AI-derived values (only for non-empty overrides)."""
    for k, v in (overrides or {}).items():
        if v in (None, '', []):
            continue
        profile[k] = v
    return profile


def save_profile_overrides(brand, overrides):
    """Persist salesperson edits and immediately reflect them in client_profile."""
    clean = {k: v for k, v in (overrides or {}).items() if k in _EDITABLE_KEYS}
    brand.profile_overrides = json.dumps(clean)
    profile = json.loads(brand.client_profile) if brand.client_profile else {}
    profile = _apply_overrides(profile, clean)
    brand.client_profile = json.dumps(profile)
    if not brand.profile_built_at:
        brand.profile_built_at = datetime.utcnow()
    db.session.commit()
    return profile


def ensure_profile(brand, force=False):
    """Build the client profile if missing/stale. Returns the profile dict.

    Renders the client's website in a headless browser to get both readable text
    AND a screenshot, then has GPT-5.5 vision interpret the screenshot — so the
    profile understands their design/products/vibe, not just words. Falls back to
    plain scraping, then to the info on file, so it always produces a profile.

    Salesperson edits (profile_overrides) are merged on top every time, so a
    re-scrape refreshes the AI-derived fields without ever clobbering corrections.
    """
    overrides = _load_overrides(brand)
    if not force and not _profile_stale(brand):
        return _apply_overrides(json.loads(brand.client_profile), overrides)

    rendered = radar.render_page(brand.website_url) if brand.website_url else {}
    screenshot = rendered.get('screenshot')
    text = rendered.get('text', '')
    blocked = rendered.get('blocked', False)
    reason = rendered.get('reason', '')
    source = 'site' if text else 'none'
    if not text and brand.website_url:  # rendering failed — try plain scrape
        scraped = radar.scrape_website(brand.website_url)
        text = scraped.get('text', '')
        if text:
            source = 'site'
        else:
            blocked = scraped.get('blocked', blocked)
            reason = scraped.get('reason', reason)

    # The site is bot-blocked (Truline's is) → research the business via GOOGLE
    # (SerpAPI). Google isn't blocked, so this gives us real grounded facts —
    # knowledge panel, address, services, snippets — with no site access at all.
    if not text and radar.serp_configured():
        query = f"{brand.name} {brand.industry or ''}".strip()
        location = ''
        for key in ('service_area', 'service_area_cities'):
            existing = (json.loads(brand.client_profile) if brand.client_profile else {}).get(key)
            if existing:
                location = existing[0] if isinstance(existing, list) else existing
                break
        serp_text = radar.fetch_serp_business_text(query, location=location or '')
        if serp_text:
            text = serp_text
            source = 'google'
            blocked = False

    profile = _build_profile(brand, text, screenshot)
    profile['built_at'] = datetime.utcnow().isoformat()
    profile['scraped'] = bool(text)
    profile['source'] = source
    profile['scrape_blocked'] = bool(brand.website_url and not text)
    profile['scrape_reason'] = reason if (brand.website_url and not text) else ''
    profile['screenshot_path'] = _save_screenshot(brand, screenshot)
    profile = _apply_overrides(profile, overrides)  # human edits always win
    brand.client_profile = json.dumps(profile)
    brand.profile_built_at = datetime.utcnow()
    db.session.commit()
    return profile


def _save_screenshot(brand, png):
    """Persist the profile screenshot for preview in the UI. Returns static path or None."""
    if not png:
        return None
    try:
        folder = os.path.join('static', 'uploads')
        os.makedirs(folder, exist_ok=True)
        fname = f"profile_{brand.id}.png"
        with open(os.path.join(folder, fname), 'wb') as f:
            f.write(png)
        return f"uploads/{fname}"
    except Exception as e:
        logger.info(f"could not save screenshot: {e}")
        return None


def _build_profile(brand, text, screenshot=None):
    base = {
        'business_name': brand.name,
        'industry': brand.industry or 'general',
        'website': brand.website_url or '',
        'description': brand.description or '',
    }

    # Vision: let the model SEE the website and describe design/products/vibe.
    vision_notes = ''
    if ai_configured() and screenshot:
        try:
            vision_notes = _openai_vision(
                screenshot,
                "This is a screenshot of a business's website. Describe in detail: what the "
                "business sells, their design vibe / brand feel, featured products or services, "
                "dominant brand colors, and the overall quality of their online presence.",
                max_tokens=1400,  # GPT-5.x spends some budget on reasoning — leave headroom
            )
        except Exception as e:
            logger.warning(f"vision profile failed for {brand.name}: {e}")

    if ai_configured() and (text or vision_notes):
        try:
            out = _openai_chat(
                system=(
                    "You build a COMPREHENSIVE, structured profile of a local business so a "
                    "marketing engine never has to ask the owner basic questions. Reply ONLY "
                    "with a JSON object with these keys:\n"
                    "  what_they_sell (string), offers (array of their specific offers/services), "
                    "voice (string, e.g. 'friendly local expert'), tone (string: 1-3 adjectives), "
                    "proof_points (array: awards, years in business, certifications, guarantees, "
                    "review counts — only ones actually stated), service_area (string: the "
                    "geographic area they serve, e.g. 'Columbus, OH and surrounding suburbs'), "
                    "service_area_cities (array of specific city/region names they serve), "
                    "target_audience (string), differentiators (array: why pick them over a "
                    "competitor), brand_colors (array of color names), "
                    "banned_topics (array: subjects this business should NOT post about — infer "
                    "sensibly, e.g. politics, religion, competitor names, discounts they don't "
                    "offer), keywords (array of 5-8 short search terms).\n"
                    "CRITICAL: Use ONLY facts present in the supplied website text/visual "
                    "analysis or the business info. DO NOT GUESS a city, service area, award, or "
                    "claim. If a fact (especially the service area) is not clearly stated, return "
                    "an empty string or empty array for it — never fabricate geography or proof. "
                    "A wrong service area causes posts that name the wrong city."
                ),
                prompt=f"Business: {brand.name} (industry: {brand.industry or 'unknown'}).\n"
                       f"Info on file: {brand.description or '(none)'}\n"
                       f"Website text:\n{text[:3500]}\n\n"
                       f"Visual analysis of their website (from a screenshot):\n{vision_notes}",
                max_tokens=2500,  # GPT-5.x reasoning overhead — 900 risked an empty return
            )
            data = _parse_json(out, {})
            if isinstance(data, dict):
                base.update(data)
        except Exception as e:
            logger.warning(f"profile AI structuring failed for {brand.name}: {e}")

    base['vision_used'] = bool(vision_notes)
    base['vision_notes'] = vision_notes
    base.setdefault('voice', 'professional and approachable')
    base.setdefault('tone', base.get('voice', 'professional and approachable'))
    base.setdefault('keywords', _fallback_keywords(brand))
    base.setdefault('what_they_sell', brand.description or f"{brand.industry or 'services'}")
    # Never fabricate geography — leave blank if unknown so it's a visible gap to fill.
    base.setdefault('service_area', '')
    base.setdefault('service_area_cities', [])
    base.setdefault('offers', [])
    base.setdefault('proof_points', [])
    base.setdefault('differentiators', [])
    base.setdefault('banned_topics', [])
    base.setdefault('target_audience', '')
    return base


def _fallback_keywords(brand):
    industry = (brand.industry or 'business').lower()
    return [industry, f"{industry} near me", f"best {industry}", brand.name]


# ---------------------------------------------------------------------------
# 2. The Radar — gather fresh, time-stamped signals
# ---------------------------------------------------------------------------
def gather_radar(brand, profile):
    keywords = profile.get('keywords') or _fallback_keywords(brand)
    competitor_urls = [c.website_url for c in Competitor.query.filter_by(brand_id=brand.id).all()
                       if c.website_url]

    signals = []
    signals += radar.fetch_events(country='US', days=30)
    signals += radar.fetch_trends(keywords)
    signals += radar.fetch_news(keywords)
    signals += radar.fetch_competitor_intel(competitor_urls)
    # Dormant feeds (activate when keys/connectors are added): reviews, local events.
    signals += radar.fetch_reviews(brand)
    signals += radar.fetch_local_events(brand)
    # Client news from their own site (recent promos/announcements) — best effort.
    site = radar.scrape_website(brand.website_url, max_chars=1500) if brand.website_url else {}
    if site.get('text'):
        signals.append(radar._signal('client_news', f"{brand.name} site snapshot",
                                     site['text'][:280], brand.website_url))

    by_feed = {}
    for s in signals:
        by_feed.setdefault(s['feed'], 0)
        by_feed[s['feed']] += 1
    return {'signals': signals, 'by_feed': by_feed, 'gathered_at': datetime.utcnow().isoformat()}


# ---------------------------------------------------------------------------
# 3. The Strategist
#    (a) a PERSISTENT living marketing plan (strategy, maintained over time)
#    (b) per-cycle post ideas, grounded in the plan + today's fresh signals
# ---------------------------------------------------------------------------
PLAN_MAX_AGE_DAYS = 30   # refresh the strategy at least this often (unless locked)

# Fields the salesperson can hand-edit on the client page. (key, label, kind).
EDITABLE_PLAN_FIELDS = [
    ('positioning', 'Positioning (one sentence vs the big competitor)', 'text'),
    ('content_pillars', 'Content pillars (recurring themes)', 'list'),
    ('target_geographies', 'Target geographies', 'list'),
    ('primary_offers', 'Offers to promote', 'list'),
    ('platform_mix', 'Platforms', 'list'),
    ('cadence_per_week', 'Posts per week', 'int'),
    ('seasonal_hooks', 'Seasonal / upcoming hooks', 'list'),
    ('competitor_angle', 'How we out-position competitors', 'text'),
    ('banned_topics', 'Banned topics (never post about)', 'list'),
    ('notes', 'Salesperson notes', 'text'),
]
_EDITABLE_PLAN_KEYS = {k for k, _, _ in EDITABLE_PLAN_FIELDS}


def _plan_stale(brand):
    plan = _load_plan(brand)
    if not plan:
        return True
    if plan.get('locked'):           # a human edited it — only `force` rebuilds
        return False
    if not brand.marketing_plan_updated_at:
        return True
    return (datetime.utcnow() - brand.marketing_plan_updated_at) > timedelta(days=PLAN_MAX_AGE_DAYS)


def _load_plan(brand):
    if not getattr(brand, 'marketing_plan', None):
        return None
    try:
        data = json.loads(brand.marketing_plan)
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def ensure_marketing_plan(brand, profile=None, force=False):
    """Return the persistent marketing plan, building/refreshing it if stale.

    The plan is the client's LIVING strategy (BLUEPRINT layer 3). Per-cycle post
    ideas are grounded in it. A human-edited (locked) plan is preserved unless
    `force=True`. Geography and banned topics inherit from the profile so the
    engine never has to ask — and never leaks a wrong city from a news headline.
    """
    if not force and not _plan_stale(brand):
        return _load_plan(brand)
    if profile is None:
        profile = ensure_profile(brand)
    prev = _load_plan(brand) or {}
    plan = _build_marketing_plan(brand, profile)
    # Preserve salesperson notes across a regeneration.
    if prev.get('notes'):
        plan['notes'] = prev['notes']
    plan['built_at'] = datetime.utcnow().isoformat()
    plan['locked'] = False
    brand.marketing_plan = json.dumps(plan)
    brand.marketing_plan_updated_at = datetime.utcnow()
    db.session.commit()
    return plan


def save_marketing_plan(brand, fields):
    """Persist a salesperson-edited plan and LOCK it (engine won't auto-overwrite)."""
    plan = _load_plan(brand) or {}
    clean = {k: v for k, v in (fields or {}).items() if k in _EDITABLE_PLAN_KEYS}
    plan.update(clean)
    plan['locked'] = True
    plan['source'] = 'manual'
    plan.setdefault('built_at', datetime.utcnow().isoformat())
    brand.marketing_plan = json.dumps(plan)
    brand.marketing_plan_updated_at = datetime.utcnow()
    db.session.commit()
    return plan


def _build_marketing_plan(brand, profile):
    geos = profile.get('service_area_cities') or (
        [profile['service_area']] if profile.get('service_area') else [])
    base = {
        'positioning': '',
        'content_pillars': [],
        'target_geographies': geos,                       # inherit corrected geography
        'primary_offers': profile.get('offers', [])[:5],
        'platform_mix': ['facebook', 'instagram'],
        'cadence_per_week': 2,
        'seasonal_hooks': [],
        'competitor_angle': '',
        'banned_topics': profile.get('banned_topics', []),  # inherit banned topics
        'notes': '',
        'source': 'fallback',
    }
    if ai_configured():
        try:
            out = _openai_chat(
                system=(
                    "You are a senior local-marketing strategist who has just studied THIS "
                    "specific business. Write a PERSISTENT marketing plan (the standing strategy, "
                    "not individual posts) that makes it out-market a bigger competitor.\n"
                    "Be SPECIFIC to this business — reference its actual offers, proof points, and "
                    "service area. BAN generic filler that would apply to any company ('engage "
                    "your audience', 'post consistently', 'showcase quality', 'build brand "
                    "awareness'). Every pillar and the competitor_angle must name a concrete, "
                    "checkable thing about THIS business (a specific service, a real guarantee, a "
                    "named neighborhood, a season that drives their demand). If a pillar could be "
                    "copy-pasted onto a competitor, rewrite it.\n"
                    "Reply ONLY with a JSON object: positioning (string, one specific sentence), "
                    "content_pillars (array of 3-5 concrete recurring themes), target_geographies "
                    "(array), primary_offers (array), platform_mix (array from "
                    "facebook/instagram/linkedin), cadence_per_week (integer 1-7), seasonal_hooks "
                    "(array of upcoming angles tied to this trade), competitor_angle (string: the "
                    "specific wedge vs local competitors), banned_topics (array).\n"
                    "CRITICAL: ground everything in the profile facts. For target_geographies use "
                    "ONLY the profile's service area / cities — never invent a city; leave it "
                    "empty if unknown. Do NOT fabricate offers or proof the profile doesn't state. "
                    "Never use 'not X but Y' / 'it's not X, it's Y' antithesis phrasing anywhere."
                ),
                prompt=f"Business profile (the only facts you may use):\n{json.dumps(profile)[:2200]}",
                # GPT-5.x burns a large, prompt-dependent share of the budget on
                # reasoning; complex prompts like this returned EMPTY at 1000 and
                # silently fell back to the generic template. 2800 leaves real room.
                max_tokens=2800,
            )
            data = _parse_json(out, {})
            if isinstance(data, dict) and data:
                for k in base:
                    if k in data and data[k] not in (None, '', []):
                        base[k] = data[k]
                base['source'] = 'ai'
                # Geography/banned topics from the profile are authoritative — merge,
                # but never let the model drop a known service area.
                if geos and not base.get('target_geographies'):
                    base['target_geographies'] = geos
                if profile.get('banned_topics'):
                    base['banned_topics'] = sorted(set(
                        list(base.get('banned_topics', [])) + list(profile['banned_topics'])))
        except Exception as e:
            logger.warning(f"marketing plan AI build failed for {brand.name}: {e}")
    return base


def build_plan(brand, profile, signals, plan=None, count=4):
    if ai_configured() and signals:
        try:
            return _ai_plan(brand, profile, signals, plan, count)
        except Exception as e:
            logger.warning(f"AI plan failed for {brand.name}: {e}")
    return _fallback_plan(brand, profile, signals, count)


def _ai_plan(brand, profile, signals, plan, count):
    signal_lines = "\n".join(
        f"- [{s['feed']}] {s['title']} — {s['detail']} (source: {s['source']})"
        for s in signals[:25]
    )
    plan = plan or {}
    geos = plan.get('target_geographies') or profile.get('service_area_cities') \
        or ([profile['service_area']] if profile.get('service_area') else [])
    banned = sorted(set(list(plan.get('banned_topics', [])) + list(profile.get('banned_topics', []))))
    plan_ctx = (
        f"Standing marketing plan to follow:\n"
        f"- Positioning: {plan.get('positioning') or '(n/a)'}\n"
        f"- Content pillars: {', '.join(plan.get('content_pillars', [])) or '(n/a)'}\n"
        f"- Offers to promote: {', '.join(plan.get('primary_offers', [])) or '(n/a)'}\n"
        f"- Competitor angle: {plan.get('competitor_angle') or '(n/a)'}\n"
    )
    geo_rule = (
        f"Geography rule: this business serves {', '.join(geos)}. Only ever reference these "
        f"locations. NEVER name a city or region from a news headline or trend — those are "
        f"signals about the wider world, not where the client operates."
        if geos else
        "Geography rule: the service area is unknown — do NOT name any city or region in posts."
    )
    banned_rule = (f"Never post about: {', '.join(banned)}." if banned else "")
    out = _openai_chat(
        system="You are a senior local-marketing strategist. Build a short social plan that "
               "makes a small business outshine bigger competitors. CRITICAL: ground every "
               "idea in the REAL SIGNALS provided and the standing plan — do not invent facts, "
               "events, or locations. Reply ONLY with a JSON array of objects with keys: angle "
               "(string), grounded_in (string: which signal/fact), platform (one of "
               "facebook/instagram/linkedin), cta (string).",
        prompt=f"Business profile:\n{json.dumps(profile)[:1200]}\n\n"
               f"{plan_ctx}\n{geo_rule}\n{banned_rule}\n\n"
               f"REAL SIGNALS (only use these for timely hooks):\n{signal_lines}\n\n"
               f"Produce {count} post ideas that advance the plan's pillars. Vary angles and platforms.",
        max_tokens=2800,  # GPT-5.x reasoning starved this at 900 → empty → generic fallback
    )
    plan_out = _parse_json(out, [])
    cleaned = []
    for b in plan_out[:count] if isinstance(plan_out, list) else []:
        if isinstance(b, dict) and b.get('angle'):
            cleaned.append({
                'angle': str(b.get('angle')),
                'grounded_in': str(b.get('grounded_in', '')),
                'platform': str(b.get('platform', 'facebook')).lower(),
                'cta': str(b.get('cta', '')),
            })
    return cleaned or _fallback_plan(brand, profile, signals, count)


def _fallback_plan(brand, profile, signals, count):
    """No-AI plan: still grounded in real signals where available."""
    facts = [f"{s['title']} — {s['detail']}" for s in signals] or \
            [f"what makes {brand.name} different", "a customer favorite", "a seasonal offer"]
    plan = []
    for i in range(count):
        plan.append({
            'angle': f"Post tied to: {facts[i % len(facts)]}",
            'grounded_in': facts[i % len(facts)],
            'platform': ['facebook', 'instagram', 'linkedin'][i % 3],
            'cta': 'Contact us today.',
        })
    return plan


# ---------------------------------------------------------------------------
# 4. The Studio — write each post + quality gate
# ---------------------------------------------------------------------------
QUALITY_CRITERIA = ['coherent', 'relevant', 'compelling', 'fresh',
                    'unique', 'creative', 'edgy', 'worth_paying']


def write_post(brand, profile, brief):
    if ai_configured():
        geos = profile.get('service_area_cities') or (
            [profile['service_area']] if profile.get('service_area') else [])
        banned = profile.get('banned_topics', [])
        geo_rule = (
            f"This business serves {', '.join(geos)} — only ever name these locations. "
            f"NEVER mention any other city/region (e.g. one from a news headline)."
            if geos else
            "The service area is unknown, so do NOT name any city or region in the caption."
        )
        banned_rule = (f" Never mention: {', '.join(banned)}." if banned else "")
        try:
            text = _openai_chat(
                system="You are an expert social media copywriter. Write ONE ready-to-post "
                       "caption (under 280 chars) in the business's voice, grounded in the "
                       "given angle/fact. Do NOT restate the strategy or the word 'angle' — "
                       "write the actual customer-facing post. 1-3 relevant hashtags, an emoji "
                       "or two, and the CTA. Do not invent facts, claims, or locations. "
                       "Never use 'not X but Y' / 'it's not X, it's Y' antithesis phrasing. "
                       "Reply with ONLY the caption text.",
                prompt=f"Business: {brand.name}. Voice: {profile.get('voice')}. "
                       f"What they sell: {profile.get('what_they_sell')}.\n"
                       f"{geo_rule}{banned_rule}\n"
                       f"Angle: {brief['angle']}\nGrounded in (real): {brief['grounded_in']}\n"
                       f"Call to action: {brief['cta']}",
                # GPT-5.x spends part of the budget on reasoning; 200 left no room
                # for the caption and it fell back to a template. Give headroom.
                max_tokens=1000,
            )
            text = _strip_fences(text).strip('"').strip()
            if text:
                return text
        except Exception as e:
            logger.warning(f"write_post failed for {brand.name}: {e}")
    # Fallback
    return f"{brief['angle']} — {brand.name}. {brief['cta']}"


def quality_gate(text, profile):
    """Score the 8 criteria (1-10). Returns (passed, scores, avg). AI if available."""
    if not ai_configured():
        return True, {}, None
    try:
        out = _openai_chat(
            system="You are a strict content quality judge. Score this social post 1-10 on each "
                   "of: coherent, relevant, compelling, fresh, unique, creative, edgy, "
                   "worth_paying. Reply ONLY with a JSON object of those keys to integer scores.",
            prompt=f"Business voice: {profile.get('voice')}\nPost:\n{text}",
            max_tokens=800,  # reasoning headroom so the score JSON isn't starved to empty
        )
        scores = _parse_json(out, {})
        nums = [float(scores.get(c, 0)) for c in QUALITY_CRITERIA if c in scores]
        avg = sum(nums) / len(nums) if nums else 0
        # GPT-5.x grades these 8 criteria harshly (esp. edgy/unique/worth_paying),
        # so the bar is calibrated to that distribution. Configurable via env.
        threshold = float(os.environ.get('QUALITY_MIN', '5.0'))
        return (avg >= threshold), scores, round(avg, 1)
    except Exception as e:
        logger.info(f"quality_gate skipped: {e}")
        return True, {}, None


def generate_video(brand, profile, brief):
    """Generate a video for the post. DORMANT — real AI video (Veo/Pika/Sora)
    needs a provider key. Returns a path or None. Scaffolded for the Pro tier so
    it activates when a video provider is configured."""
    if not os.environ.get('VIDEO_PROVIDER_API_KEY'):
        return None
    # Plug a real video provider call here when a key is configured.
    return None


def studio(brand, profile, plan):
    """Write + quality-check each brief; add image (Plus+) and video (Pro+) per tier.

    Returns list of {content, quality, brief, image_path, video_path}.
    """
    make_images = wants_images(brand)
    make_video = wants_video(brand)
    posts = []
    for brief in plan:
        text = write_post(brand, profile, brief)
        passed, scores, avg = quality_gate(text, profile)
        if not passed:  # one regeneration attempt
            text = write_post(brand, profile, brief)
            passed, scores, avg = quality_gate(text, profile)

        image_path = None
        if make_images:
            try:
                png = _openai_image(_image_prompt(brand, profile, brief, text))
                image_path = _save_post_media(brand, png, kind='img', ext='png')
            except Exception as e:
                logger.warning(f"image generation failed for {brand.name}: {e}")

        video_path = None
        if make_video:
            try:
                video_path = generate_video(brand, profile, brief)
            except Exception as e:
                logger.info(f"video generation skipped: {e}")

        posts.append({'content': text, 'quality_score': avg, 'quality_passed': passed,
                      'brief': brief, 'image_path': image_path, 'video_path': video_path})
    return posts


# ---------------------------------------------------------------------------
# 5. Scheduling
# ---------------------------------------------------------------------------
def _automation_campaign(brand):
    camp = Campaign.query.filter_by(brand_id=brand.id, campaign_type='automation').first()
    if not camp:
        camp = Campaign(id=str(uuid.uuid4()), user_id=brand.user_id, brand_id=brand.id,
                        title=f"Automation — {brand.name}", campaign_type='automation',
                        status='active', campaign_goal='engagement')
        db.session.add(camp)
        db.session.commit()
    return camp


def schedule_posts(brand, posts, first_delay_minutes=1):
    accounts = SocialAccount.query.filter_by(brand_id=brand.id, is_active=True).all()
    if not accounts:
        return {'scheduled': 0, 'reason': 'no connected accounts for this client'}
    camp = _automation_campaign(brand)
    cadence = max(1, brand.posting_frequency_days or 3)
    base = datetime.utcnow() + timedelta(minutes=first_delay_minutes)
    created = 0
    for idx, post in enumerate(posts):
        when = base + timedelta(days=cadence * idx)
        # Prefer the platform the strategist chose, but only if connected; else all.
        brief_platform = (post.get('brief') or {}).get('platform')
        targets = [a for a in accounts if a.platform == brief_platform] or accounts
        for acct in targets:
            db.session.add(SocialPost(
                user_id=brand.user_id, campaign_id=camp.id, platform=acct.platform,
                content=post['content'], scheduled_for=when, status='scheduled',
                image_url=post.get('image_path'), video_url=post.get('video_path'),
            ))
            created += 1
    db.session.commit()
    return {'scheduled': created, 'platforms': sorted({a.platform for a in accounts})}


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------
def run_cycle(brand, post_count=4):
    profile = ensure_profile(brand)
    marketing_plan = ensure_marketing_plan(brand, profile)
    radar_data = gather_radar(brand, profile)
    plan = build_plan(brand, profile, radar_data['signals'], marketing_plan, post_count)
    posts = studio(brand, profile, plan)
    sched = schedule_posts(brand, posts)

    # Persist a snapshot for the UI (keeps keys the panel already reads).
    snapshot = {
        'mode': 'live' if ai_configured() else 'simulated',
        'generated_at': datetime.utcnow().isoformat(),
        'profile_scraped': profile.get('scraped', False),
        'by_feed': radar_data['by_feed'],
        'signals': radar_data['signals'][:25],
        'plan': plan,
        'trends': [{'topic': s['title']} for s in radar_data['signals'][:6]],  # back-compat
        'summary': (f"{('Live' if ai_configured() else 'Simulated')} cycle: "
                    f"{sum(radar_data['by_feed'].values())} fresh signals "
                    f"({', '.join(f'{k}:{v}' for k, v in radar_data['by_feed'].items()) or 'none'}); "
                    f"{len(plan)} grounded ideas."),
    }
    brand.research_snapshot = json.dumps(snapshot)
    brand.last_research_at = datetime.utcnow()
    db.session.commit()

    summary = {
        'client': brand.name, 'mode': snapshot['mode'],
        'research_summary': snapshot['summary'],
        'posts_generated': len(posts), 'posts_scheduled': sched.get('scheduled', 0),
        'note': sched.get('reason'), 'ran_at': snapshot['generated_at'],
    }
    logger.info(f"Automation cycle for {brand.name}: {summary}")
    return summary


def due_for_refresh(brand):
    if not brand.automation_enabled:
        return False
    if not brand.last_research_at:
        return True
    age_days = (datetime.utcnow() - brand.last_research_at).total_seconds() / 86400
    return age_days >= max(1, brand.posting_frequency_days or 3)


def run_due_clients():
    ran = []
    for brand in Brand.query.filter_by(automation_enabled=True).all():
        if due_for_refresh(brand):
            try:
                ran.append(run_cycle(brand))
            except Exception as e:
                logger.error(f"Automation cycle failed for {brand.name}: {e}")
    return ran
