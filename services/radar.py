"""
The Radar — real, fresh intelligence feeds for the marketing engine.

Each function returns REAL data (no AI invention) with graceful fallbacks, and
every signal is time-stamped so the Strategist can enforce freshness. Feeds that
need API keys/connectors are dormant stubs until configured; the no-key feeds
(website scrape, Google Trends, holiday/events calendar, competitor scrape) work
now. See docs/BLUEPRINT.md.
"""

import logging
import re
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def _signal(feed, title, detail='', source=''):
    return {
        'feed': feed,
        'title': title,
        'detail': detail,
        'source': source,
        'observed_at': datetime.utcnow().isoformat(),
    }


# ---------------------------------------------------------------------------
# Website scrape (powers the Client Profile + client-news feed)
# ---------------------------------------------------------------------------
_UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
       '(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36')

# Substrings that signal a blocked / error / consent page rather than real content.
_JUNK_MARKERS = ('technical difficulties', 'access denied', 'are you a robot',
                 'enable javascript', 'captcha', 'request blocked', '403 forbidden',
                 'this website uses cookies')


def _looks_like_junk(text):
    if len(text) < 300:
        return True
    low = text.lower()
    return any(m in low for m in _JUNK_MARKERS)


def scraping_api_configured():
    """True if a bot-bypass scraping API is available (see _scraping_api_fetch)."""
    import os
    return bool(os.environ.get('BRIGHTDATA_API_KEY') or os.environ.get('SCRAPER_API_URL'))


def _serp_key():
    import os
    return os.environ.get('SERP_API_KEY') or os.environ.get('SERPAPI_KEY')


def serp_configured():
    """True if a SerpAPI key is set — lets us research a business via GOOGLE
    (knowledge panel + organic results) instead of its own site. This bypasses
    site bot-protection entirely (Google doesn't block us the way client sites do),
    so it's the practical answer when a client's website can't be read directly."""
    return bool(_serp_key())


def fetch_serp_business_text(query, location='', max_chars=4500):
    """Aggregate a business's PUBLIC info from Google via SerpAPI into profile text.

    Returns real, grounded text (knowledge panel facts + top organic snippets +
    local listing) or '' if unavailable. Used as the profile source when the
    client's own website is bot-blocked (see automation_engine.ensure_profile).
    """
    key = _serp_key()
    if not key or not query:
        return ''
    try:
        import requests
    except Exception:
        return ''
    params = {'engine': 'google', 'q': query, 'api_key': key, 'num': '8', 'hl': 'en'}
    if location:
        params['location'] = location
    try:
        r = requests.get('https://serpapi.com/search', params=params, timeout=45)
        if r.status_code != 200:
            logger.info(f"SerpAPI HTTP {r.status_code} for '{query}'")
            return ''
        d = r.json()
    except Exception as e:
        logger.info(f"SerpAPI request failed for '{query}': {e}")
        return ''
    if d.get('error'):
        logger.info(f"SerpAPI error for '{query}': {d['error']}")
        return ''
    parts = []
    kg = d.get('knowledge_graph') or {}
    if kg:
        for k in ('title', 'type', 'description', 'address', 'phone', 'website'):
            v = kg.get(k)
            if isinstance(v, str) and v:
                parts.append(f"{k}: {v}")
        # scalar extras (rating, hours, service options, etc.)
        for k, v in kg.items():
            if k in ('title', 'type', 'description', 'address', 'phone', 'website'):
                continue
            if isinstance(v, (str, int, float)) and str(v).strip():
                parts.append(f"{k}: {v}")
    # Google Business / local pack
    for loc in (d.get('local_results', {}) or {}).get('places', [])[:2] if isinstance(d.get('local_results'), dict) else []:
        bits = [loc.get(x) for x in ('title', 'type', 'address', 'phone') if loc.get(x)]
        if bits:
            parts.append('local: ' + ' | '.join(str(b) for b in bits))
    # Organic result snippets (the business's own pages + directories)
    for o in (d.get('organic_results') or [])[:6]:
        t = o.get('title') or ''
        s = o.get('snippet') or ''
        if s:
            parts.append(f"{t}: {s}")
    text = '\n'.join(parts).strip()
    return text[:max_chars]


def _scraping_api_fetch(url):
    """Fetch a page THROUGH a scraping API that bypasses bot protection.

    Many small-business sites (even the client's own — trulineroofing.com does)
    sit behind Cloudflare/WAF/bot protection that refuses our direct request and
    headless browser. A scraping API renders + unblocks them. This is the
    BLUEPRINT's "scraping API for blocked sites" connector. Dormant until a key
    is set. Provider-agnostic:

      • Bright Data Web Unlocker — set BRIGHTDATA_API_KEY (+ optional
        BRIGHTDATA_ZONE, default 'web_unlocker1').
      • Any provider — set SCRAPER_API_URL to a template containing '{url}'
        (URL-encoded), e.g. ScraperAPI:
        https://api.scraperapi.com/?api_key=XXX&render=true&url={url}
        or ScrapingBee/ScrapingAnt/Zyte equivalents.

    Returns rendered HTML (str) or None.
    """
    import os
    try:
        import requests
    except Exception:
        return None
    # 1) Bright Data Web Unlocker
    key = os.environ.get('BRIGHTDATA_API_KEY')
    if key:
        try:
            zone = os.environ.get('BRIGHTDATA_ZONE', 'web_unlocker1')
            r = requests.post('https://api.brightdata.com/request',
                              headers={'Authorization': f'Bearer {key}',
                                       'Content-Type': 'application/json'},
                              json={'zone': zone, 'url': url, 'format': 'raw'},
                              timeout=60)
            if r.status_code == 200 and r.text and len(r.text) > 200:
                return r.text
            logger.info(f"Bright Data fetch for {url}: HTTP {r.status_code}")
        except Exception as e:
            logger.info(f"Bright Data fetch failed for {url}: {e}")
    # 2) Generic provider via URL template
    tmpl = os.environ.get('SCRAPER_API_URL')
    if tmpl and '{url}' in tmpl:
        try:
            from urllib.parse import quote
            api_url = tmpl.replace('{url}', quote(url, safe=''))
            r = requests.get(api_url, timeout=60)
            if r.status_code == 200 and r.text and len(r.text) > 200:
                return r.text
            logger.info(f"scraping API fetch for {url}: HTTP {r.status_code}")
        except Exception as e:
            logger.info(f"scraping API fetch failed for {url}: {e}")
    return None


def scrape_website(url, max_chars=6000):
    """Fetch readable text + title from a URL. Returns {} on failure or junk.

    Uses a real browser User-Agent (many sites block default fetchers) and
    rejects blocked/consent/error pages so we never ground content in junk.
    NOTE: plain HTTP scraping is blocked by many modern sites; robust scraping
    at scale needs a scraping API (a dormant connector — see BLUEPRINT.md).
    """
    if not url:
        return {}
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    html = None
    blocked = False
    try:
        import requests
        r = requests.get(url, headers={'User-Agent': _UA, 'Accept-Language': 'en-US,en;q=0.9'},
                         timeout=15)
        if r.status_code == 200 and r.text:
            html = r.text
        elif r.status_code in (401, 403, 406, 429, 503):
            blocked = True  # bot protection / rate limit
    except Exception as e:
        blocked = True  # connection reset etc. — usually bot protection
        logger.info(f"requests fetch failed for {url}: {e}")

    def _extract(h):
        import trafilatura
        return (trafilatura.extract(h, include_comments=False, include_tables=False) or '').strip()

    try:
        import trafilatura
        if html is None:
            html = trafilatura.fetch_url(url)
        text = _extract(html) if html else ''
        # Direct fetch blocked or junk → try the scraping API (bypasses WAF/bots).
        if (not text or _looks_like_junk(text)) and scraping_api_configured():
            api_html = _scraping_api_fetch(url)
            if api_html:
                html = api_html
                text = _extract(html)
        if not text or _looks_like_junk(text):
            reason = ('This site blocks automated reading (bot protection). '
                      'Add a scraping API key or fill the profile in by hand.'
                      if (blocked or not scraping_api_configured())
                      else 'The page had no readable content.')
            logger.info(f"scrape_website could not read {url}: {reason}")
            return {'url': url, 'text': '', 'blocked': True, 'reason': reason}
        title = ''
        try:
            meta = trafilatura.extract_metadata(html)
            title = (meta.title if meta else '') or ''
        except Exception:
            pass
        return {'url': url, 'title': title.strip(), 'text': text[:max_chars]}
    except Exception as e:
        logger.warning(f"scrape_website failed for {url}: {e}")
        return {'url': url, 'text': '', 'blocked': True,
                'reason': f'Could not read the site ({type(e).__name__}).'}


def render_page(url, full_page=False):
    """Render a page in a headless browser and return rendered text + a screenshot.

    Rendering (vs plain HTTP) both (a) reads JS-heavy pages and (b) gets past many
    sites that block simple scraping, and (c) gives us a screenshot for GPT-5.5
    vision. Returns {} on failure. Heavier than scrape_website — use for the
    Client Profile (built infrequently), not every per-cycle fetch.
    """
    if not url:
        return {}
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    png = html = title = None
    render_failed = False
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            try:
                page = browser.new_page(viewport={'width': 1280, 'height': 900}, user_agent=_UA)
                page.goto(url, wait_until='domcontentloaded', timeout=30000)
                page.wait_for_timeout(2500)
                png = page.screenshot(full_page=full_page)
                html = page.content()
                title = page.title()
            finally:
                browser.close()
    except Exception as e:
        render_failed = True
        logger.info(f"render_page failed for {url}: {e}")

    text = ''
    if html:
        try:
            import trafilatura
            text = (trafilatura.extract(html, include_comments=False, include_tables=False) or '').strip()
        except Exception:
            pass
    if _looks_like_junk(text):
        text = ''

    # Browser blocked or produced junk → try the scraping API for the TEXT
    # (no screenshot, but at least the profile gets real content).
    if not text and scraping_api_configured():
        api_html = _scraping_api_fetch(url)
        if api_html:
            try:
                import trafilatura
                t = (trafilatura.extract(api_html, include_comments=False, include_tables=False) or '').strip()
                if t and not _looks_like_junk(t):
                    text = t
            except Exception:
                pass

    if not text and not png:
        reason = ('This site blocks automated reading (bot protection). '
                  'Add a scraping API key or fill the profile in by hand.'
                  if (render_failed or not scraping_api_configured())
                  else 'The page had no readable content.')
        return {'url': url, 'text': '', 'screenshot': None, 'blocked': True, 'reason': reason}
    return {'url': url, 'title': (title or '').strip(), 'text': text[:6000], 'screenshot': png}


# ---------------------------------------------------------------------------
# Culture & Trends (Google Trends — best effort, no key)
# ---------------------------------------------------------------------------
def fetch_trends(keywords, geo='US'):
    """Rising/related queries for a few seed keywords. Returns a list of signals."""
    out = []
    try:
        from pytrends.request import TrendReq
        pytrends = TrendReq(hl='en-US', tz=360)
        seeds = [k for k in (keywords or [])[:3] if k]
        if not seeds:
            return out
        pytrends.build_payload(seeds, timeframe='now 7-d', geo=geo)
        related = pytrends.related_queries()
        for seed in seeds:
            rising = (related.get(seed) or {}).get('rising')
            if rising is not None:
                for _, row in rising.head(3).iterrows():
                    out.append(_signal('culture_trends', str(row['query']),
                                       f"rising search related to '{seed}'", 'Google Trends'))
    except Exception as e:
        logger.info(f"fetch_trends unavailable: {e}")
    return out


# ---------------------------------------------------------------------------
# Events & Calendar (holidays/observances — real, no key)
# ---------------------------------------------------------------------------
def fetch_events(country='US', days=30):
    """Upcoming holidays/observances within `days`. Returns a list of signals."""
    out = []
    try:
        import holidays as hol
        today = datetime.utcnow().date()
        end = today + timedelta(days=days)
        cal = hol.country_holidays(country, years=[today.year, end.year])
        for d, name in sorted(cal.items()):
            if today <= d <= end:
                days_out = (d - today).days
                out.append(_signal('events', name,
                                   f"in {days_out} day(s) — {d.isoformat()}", 'Holiday calendar'))
    except Exception as e:
        logger.info(f"fetch_events unavailable: {e}")
    return out


# ---------------------------------------------------------------------------
# Competitor Intelligence (competitor website scrape — real; reviews need keys)
# ---------------------------------------------------------------------------
def fetch_competitor_intel(competitor_urls):
    """Scrape competitor sites for positioning signals. Returns a list of signals."""
    out = []
    for url in (competitor_urls or [])[:3]:
        data = scrape_website(url, max_chars=2000)
        if data.get('text'):
            snippet = re.sub(r'\s+', ' ', data['text'])[:300]
            out.append(_signal('competitor', data.get('title') or url,
                               f"competitor messaging: {snippet}", url))
    return out


def recency_window_days():
    """The Freshness Clock's recency window: signals older than this may not
    ground content (BLUEPRINT: 'never last week's data'). Env-tunable."""
    import os
    try:
        return max(1, int(os.environ.get('RECENCY_WINDOW_DAYS', '7')))
    except (ValueError, TypeError):
        return 7


def _parse_rss_date(pub):
    """Parse an RSS pubDate ('Tue, 01 Jul 2026 04:00:00 GMT'). None on failure."""
    from email.utils import parsedate_to_datetime
    try:
        dt = parsedate_to_datetime(pub)
        return dt.replace(tzinfo=None) if dt else None
    except Exception:
        return None


def fetch_news(keywords, locality='', geo='US', max_items=6):
    """Fresh, LOCAL headlines via Google News RSS (real, no key). Returns signals.

    Localized: each keyword is queried WITH the client's locality (their service
    area city/region) so the news is about their market, not the nation — a
    national headline is exactly how a wrong city once leaked into a post.
    Freshness-enforced: items older than the recency window are dropped.
    """
    out = []
    seeds = [k for k in (keywords or [])[:2] if k]
    if not seeds:
        return out
    window = timedelta(days=recency_window_days())
    now = datetime.utcnow()
    try:
        import requests
        import xml.etree.ElementTree as ET
        from urllib.parse import quote_plus
        queries = [f"{seed} {locality}".strip() for seed in seeds]
        if locality:  # plus one purely-local pulse on the area itself
            queries.append(locality)
        for q in queries:
            url = (f"https://news.google.com/rss/search?q={quote_plus(q)}"
                   f"&hl=en-{geo}&gl={geo}&ceid={geo}:en")
            r = requests.get(url, headers={'User-Agent': _UA}, timeout=12)
            if r.status_code != 200:
                continue
            root = ET.fromstring(r.content)
            for item in list(root.iterfind('.//item'))[:4]:
                title = (item.findtext('title') or '').strip()
                pub = (item.findtext('pubDate') or '').strip()
                pub_dt = _parse_rss_date(pub)
                # Freshness Clock: drop anything outside the recency window.
                if pub_dt is not None and (now - pub_dt) > window:
                    continue
                src_el = item.find('{*}source')
                src = (src_el.text if src_el is not None else 'Google News')
                if title:
                    out.append(_signal('news', title,
                                       f"headline for '{q}' — {pub or 'undated'}", src))
                if len(out) >= max_items:
                    return out
    except Exception as e:
        logger.info(f"fetch_news unavailable: {e}")
    return out


# ---------------------------------------------------------------------------
# Localization helpers — the Radar must watch the CLIENT'S market, not the nation
# ---------------------------------------------------------------------------
_STATE_ABBREVS = {
    'alabama': 'AL', 'alaska': 'AK', 'arizona': 'AZ', 'arkansas': 'AR',
    'california': 'CA', 'colorado': 'CO', 'connecticut': 'CT', 'delaware': 'DE',
    'florida': 'FL', 'georgia': 'GA', 'hawaii': 'HI', 'idaho': 'ID',
    'illinois': 'IL', 'indiana': 'IN', 'iowa': 'IA', 'kansas': 'KS',
    'kentucky': 'KY', 'louisiana': 'LA', 'maine': 'ME', 'maryland': 'MD',
    'massachusetts': 'MA', 'michigan': 'MI', 'minnesota': 'MN', 'mississippi': 'MS',
    'missouri': 'MO', 'montana': 'MT', 'nebraska': 'NE', 'nevada': 'NV',
    'new hampshire': 'NH', 'new jersey': 'NJ', 'new mexico': 'NM', 'new york': 'NY',
    'north carolina': 'NC', 'north dakota': 'ND', 'ohio': 'OH', 'oklahoma': 'OK',
    'oregon': 'OR', 'pennsylvania': 'PA', 'rhode island': 'RI', 'south carolina': 'SC',
    'south dakota': 'SD', 'tennessee': 'TN', 'texas': 'TX', 'utah': 'UT',
    'vermont': 'VT', 'virginia': 'VA', 'washington': 'WA', 'west virginia': 'WV',
    'wisconsin': 'WI', 'wyoming': 'WY',
}
_ABBREV_SET = set(_STATE_ABBREVS.values())


def locality_from_profile(profile):
    """Best locality string for feed queries from a client profile.

    Prefers the first specific city ('Charlotte NC') over the broad service_area
    ('East Coast of the U.S.'). Returns '' if geography is unknown — feeds then
    stay unlocalized rather than guessing a place.
    """
    cities = profile.get('service_area_cities') or []
    if cities:
        return str(cities[0])
    return str(profile.get('service_area') or '')


def trends_geo_from_profile(profile):
    """Google-Trends geo code for the client's state ('US-NC'), else 'US'.

    State-level is the finest granularity Trends supports reliably; it still
    beats the previous everyone-gets-national default.
    """
    text = ' '.join(
        [str(profile.get('service_area') or '')] +
        [str(c) for c in (profile.get('service_area_cities') or [])]
    ).lower()
    for name, ab in _STATE_ABBREVS.items():
        if name in text:
            return f'US-{ab}'
    # Bare abbreviations ('Charlotte NC', 'Charleston, SC')
    import re as _re
    for token in _re.findall(r'\b([A-Z]{2})\b', ' '.join(
            [str(profile.get('service_area') or '')] +
            [str(c) for c in (profile.get('service_area_cities') or [])])):
        if token in _ABBREV_SET:
            return f'US-{token}'
    return 'US'


def fetch_serp_local_news(industry, locality, max_items=4):
    """LOCAL news for the client's market via SerpAPI's Google News engine.

    'roofing Charlotte NC' style query — surfaces storms, local projects, market
    happenings a strategist can actually use. One SerpAPI search per cycle.
    Freshness-enforced via the engine's own recency. Returns signals ([] if no key).
    """
    key = _serp_key()
    if not (key and locality):
        return []
    try:
        import requests
    except Exception:
        return []
    q = f"{industry} {locality}".strip()
    try:
        r = requests.get('https://serpapi.com/search',
                         params={'engine': 'google_news', 'q': q, 'api_key': key,
                                 'hl': 'en', 'gl': 'us'},
                         timeout=45)
        if r.status_code != 200:
            return []
        d = r.json()
    except Exception as e:
        logger.info(f"fetch_serp_local_news failed for '{q}': {e}")
        return []
    out = []
    window = timedelta(days=recency_window_days())
    now = datetime.utcnow()
    for item in (d.get('news_results') or [])[:10]:
        title = (item.get('title') or '').strip()
        date_str = ((item.get('date') or '').split(',')[0]).strip()  # '07/01/2026' or relative
        # SerpAPI dates come as '07/01/2026, 04:00 PM, +0000 UTC' or '2 days ago'.
        fresh = True
        try:
            if '/' in date_str:
                dt = datetime.strptime(date_str, '%m/%d/%Y')
                fresh = (now - dt) <= window
            elif 'week' in (item.get('date') or '') or 'month' in (item.get('date') or ''):
                fresh = False
        except Exception:
            pass
        if title and fresh:
            src = (item.get('source') or {}).get('name') if isinstance(item.get('source'), dict) \
                else (item.get('source') or 'Google News')
            out.append(_signal('local_news', title, f"local news for '{q}'", src or 'Google News'))
        if len(out) >= max_items:
            break
    return out


def discover_competitors(business_name, industry, locality, exclude_domain='', limit=5):
    """Find the client's REAL local competitors via SerpAPI's Google local pack.

    'roofing contractor near Charlotte NC' → named competitors with ratings and
    review counts (out-positioning intel even when their sites block scraping).
    Returns a list of {name, website, rating, reviews, address}; [] if no key.
    """
    key = _serp_key()
    if not (key and locality):
        return []
    try:
        import requests
    except Exception:
        return []
    q = f"{industry or 'business'} near {locality}"
    try:
        r = requests.get('https://serpapi.com/search',
                         params={'engine': 'google_local', 'q': q, 'api_key': key,
                                 'hl': 'en', 'gl': 'us'},
                         timeout=45)
        if r.status_code != 200:
            return []
        d = r.json()
    except Exception as e:
        logger.info(f"discover_competitors failed for '{q}': {e}")
        return []
    own = (business_name or '').lower().strip()
    own_domain = (exclude_domain or '').lower().replace('https://', '').replace('http://', '').split('/')[0]
    out = []
    for place in (d.get('local_results') or []):
        name = (place.get('title') or '').strip()
        if not name or own and (own in name.lower() or name.lower() in own):
            continue  # never list the client as their own competitor
        website = (place.get('links') or {}).get('website') or place.get('website') or ''
        if own_domain and own_domain in (website or '').lower():
            continue
        out.append({
            'name': name,
            'website': website,
            'rating': place.get('rating'),
            'reviews': place.get('reviews'),
            'address': place.get('address') or '',
        })
        if len(out) >= limit:
            break
    return out


def competitor_signals_from_records(competitors):
    """Radar signals from stored Competitor rows' SERP intel (works even when
    competitor sites block scraping — ratings/review counts are the wedge)."""
    out = []
    for c in (competitors or [])[:5]:
        detail_bits = []
        strengths = c.strengths if isinstance(c.strengths, dict) else {}
        if strengths.get('rating') is not None:
            detail_bits.append(f"{strengths['rating']}★")
        if strengths.get('reviews') is not None:
            detail_bits.append(f"{strengths['reviews']} reviews")
        if c.description:
            detail_bits.append(str(c.description)[:120])
        out.append(_signal('competitor', f"Local competitor: {c.company_name}",
                           ' | '.join(detail_bits) or 'competitor on file',
                           c.website_url or 'Google local results'))
    return out


# Dormant feeds (need keys/connectors) — documented so the architecture is clear.
def fetch_reviews(*args, **kwargs):
    """Yelp / Google Maps reviews — needs API keys (Yelp Fusion / Google Places). Dormant."""
    return []


def fetch_local_events(*args, **kwargs):
    """Local sports / concerts / movies / conventions — needs event APIs
    (Ticketmaster, TMDB, etc.). Dormant until keys are configured."""
    return []
