# services/ingest.py
import re
from typing import List, Optional
import requests
from bs4 import BeautifulSoup
import trafilatura

# we’ll reuse your little “box” classes
from models import db

from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class SiteProfile:
    url: str = ""
    title: str = ""
    description: str = ""
    keywords: List[str] = field(default_factory=list)
    content: str = ""
    industry: str = ""
    business_name: str = ""
    contact_email: str = ""
    contact_phone: str = ""
    social_links: dict = field(default_factory=dict)
    error: Optional[str] = None


def _clean_paragraphs(text: str) -> List[str]:
    # split on blank lines or hard breaks, trim junk, drop super-short lines
    if not text:
        return []
    raw = re.split(r"\n{2,}|\r\n\r\n", text)
    cleaned = []
    for p in raw:
        p = p.strip()
        # squash multiple spaces
        p = re.sub(r"\s+", " ", p)
        if len(p) >= 40:  # skip tiny scraps
            cleaned.append(p)
    # cap at something sane so we don’t carry a phonebook around
    return cleaned[:50]

def fetch_site_profile(url: str) -> SiteProfile:
    """
    Fetches a web page and returns a SiteProfile:
    - title
    - meta description
    - meta keywords (if any)
    - cleaned main text as paragraphs
    """
    # polite browser-looking headers so fewer sites block us
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    }

    # 1) Download HTML
    resp = requests.get(url, headers=headers, timeout=20)
    resp.raise_for_status()
    html = resp.text

    # 2) Quick metadata with BeautifulSoup
    soup = BeautifulSoup(html, "lxml")

    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else None

    desc_tag = soup.find("meta", attrs={"name": "description"})
    if not desc_tag:
        # some sites use this alternate attribute
        desc_tag = soup.find("meta", attrs={"property": "og:description"})
    description = desc_tag.get("content").strip() if desc_tag and desc_tag.get("content") else None

    kw_tag = soup.find("meta", attrs={"name": "keywords"})
    raw_keywords = kw_tag.get("content") if kw_tag and kw_tag.get("content") else ""
    keywords = [k.strip() for k in raw_keywords.split(",") if k.strip()]

    # 3) Main readable text with trafilatura (does boilerplate removal)
    extracted = trafilatura.extract(html, favor_recall=True, include_comments=False)
    paragraphs = _clean_paragraphs(extracted or "")

    # 4) Very light “offers” guess (totally optional)
    offers: List[str] = []
    for p in paragraphs[:10]:
        if any(word in p.lower() for word in ["save", "free", "guarantee", "book now", "schedule", "pricing", "get started"]):
            offers.append(p[:160] + ("…" if len(p) > 160 else ""))
    offers = offers[:5]

    # 5) Brand voice placeholder (we’ll do AI later)
    brand_voice: Optional[str] = None

    return SiteProfile(
        url=url,
        title=title,
        description=description,
        keywords=keywords,
        paragraphs=paragraphs,
        brand_voice=brand_voice,
        offers=offers,
    )