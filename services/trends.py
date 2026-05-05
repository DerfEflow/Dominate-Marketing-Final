# services/trends.py
from typing import List
from models.core import TrendItem
import random

def get_trends(limit: int = 5) -> List[TrendItem]:
    """
    Temporary: returns fake trend data so we can test the rest of the pipeline.
    Later, we’ll replace with real API calls.
    """
    sample_platforms = ["youtube", "tiktok", "x"]
    sample_kinds = ["song", "hashtag", "topic"]
    sample_titles = [
        "Jet2 viral jingle remix",
        "Epic backflip dog challenge",
        "AI-generated travel tips",
        "5-minute meal hack",
        "Behind the scenes: Space launch"
    ]

    trends = []
    for _ in range(limit):
        platform = random.choice(sample_platforms)
        kind = random.choice(sample_kinds)
        title = random.choice(sample_titles)
        trend_id = f"{platform}_{kind}_{random.randint(1000, 9999)}"
        popularity = round(random.uniform(0.5, 1.0), 2)  # score between 0.5 and 1.0
        sample_url = f"https://example.com/{trend_id}"

        trends.append(
            TrendItem(
                platform=platform,
                kind=kind,
                id=trend_id,
                title=title,
                popularity_score=popularity,
                sample_url=sample_url
            )
        )

    return trends