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
    try:
        import requests
        r = requests.get(url, headers={'User-Agent': _UA, 'Accept-Language': 'en-US,en;q=0.9'},
                         timeout=15)
        if r.status_code == 200 and r.text:
            html = r.text
    except Exception as e:
        logger.info(f"requests fetch failed for {url}: {e}")
    try:
        import trafilatura
        if html is None:
            html = trafilatura.fetch_url(url)
        if not html:
            return {}
        text = (trafilatura.extract(html, include_comments=False, include_tables=False) or '').strip()
        if _looks_like_junk(text):
            logger.info(f"scrape_website rejected junk/blocked page for {url}")
            return {}
        title = ''
        try:
            meta = trafilatura.extract_metadata(html)
            title = (meta.title if meta else '') or ''
        except Exception:
            pass
        return {'url': url, 'title': title.strip(), 'text': text[:max_chars]}
    except Exception as e:
        logger.warning(f"scrape_website failed for {url}: {e}")
        return {}


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
        logger.info(f"render_page failed for {url}: {e}")
        return {}
    text = ''
    try:
        import trafilatura
        text = (trafilatura.extract(html, include_comments=False, include_tables=False) or '').strip()
    except Exception:
        pass
    if _looks_like_junk(text):
        text = ''
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
