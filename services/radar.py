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


def fetch_news(keywords, geo='US', max_items=5):
    """Fresh headlines via Google News RSS (real, no key). Returns signals.

    Grounds content in what's actually in the news for the client's topics —
    part of the Culture & Trends / Client-News awareness.
    """
    out = []
    seeds = [k for k in (keywords or [])[:2] if k]
    if not seeds:
        return out
    try:
        import requests
        import xml.etree.ElementTree as ET
        from urllib.parse import quote_plus
        for seed in seeds:
            url = (f"https://news.google.com/rss/search?q={quote_plus(seed)}"
                   f"&hl=en-{geo}&gl={geo}&ceid={geo}:en")
            r = requests.get(url, headers={'User-Agent': _UA}, timeout=12)
            if r.status_code != 200:
                continue
            root = ET.fromstring(r.content)
            for item in list(root.iterfind('.//item'))[:3]:
                title = (item.findtext('title') or '').strip()
                pub = (item.findtext('pubDate') or '').strip()
                src_el = item.find('{*}source')
                src = (src_el.text if src_el is not None else 'Google News')
                if title:
                    out.append(_signal('news', title, f"headline for '{seed}' — {pub}", src))
    except Exception as e:
        logger.info(f"fetch_news unavailable: {e}")
    return out


# Dormant feeds (need keys/connectors) — documented so the architecture is clear.
def fetch_reviews(*args, **kwargs):
    """Yelp / Google Maps reviews — needs API keys (Yelp Fusion / Google Places). Dormant."""
    return []


def fetch_local_events(*args, **kwargs):
    """Local sports / concerts / movies / conventions — needs event APIs
    (Ticketmaster, TMDB, etc.). Dormant until keys are configured."""
    return []
