# models/core.py
from typing import List, Optional

class SiteProfile:
    def __init__(self, url: str, title: Optional[str] = None,
                 description: Optional[str] = None,
                 keywords: Optional[List[str]] = None,
                 paragraphs: Optional[List[str]] = None,
                 brand_voice: Optional[str] = None,
                 offers: Optional[List[str]] = None):
        self.url = url
        self.title = title
        self.description = description
        self.keywords = keywords or []
        self.paragraphs = paragraphs or []
        self.brand_voice = brand_voice
        self.offers = offers or []

class TrendItem:
    def __init__(self, platform: str, kind: str, id: str,
                 title: Optional[str] = None, popularity_score: float = 0.0,
                 sample_url: Optional[str] = None):
        self.platform = platform      # e.g. "youtube", "tiktok", "x"
        self.kind = kind              # e.g. "song", "hashtag", "topic"
        self.id = id
        self.title = title
        self.popularity_score = popularity_score  # 0.0 to 1.0
        self.sample_url = sample_url

class Strategy:
    def __init__(self, brand_voice: str,
                 angles: List[dict],        # each dict has: name, hook, cta
                 channels: List[dict]):     # each dict has: channel, cadence_per_week, formats
        self.brand_voice = brand_voice
        self.angles = angles
        self.channels = channels