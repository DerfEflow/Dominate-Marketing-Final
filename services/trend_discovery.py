"""
Trend discovery service - wraps trend_harvester and trends_collector for unified access.
"""
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class TrendDiscoveryService:
    def __init__(self):
        self._harvester = None
        self._collector = None
        self._load_services()

    def _load_services(self):
        try:
            from services.trend_harvester import TrendHarvester
            self._harvester = TrendHarvester()
        except Exception as e:
            logger.warning(f"TrendHarvester unavailable: {e}")
        try:
            from services.trends_collector import TrendsCollector
            self._collector = TrendsCollector()
        except Exception as e:
            logger.warning(f"TrendsCollector unavailable: {e}")

    def get_trends_for_industry(self, industry: str, keywords: List[str] = None) -> Dict[str, Any]:
        """Get current trends relevant to the given industry."""
        trends = {
            "industry": industry,
            "trending_topics": [],
            "viral_formats": [],
            "recommended_hashtags": [],
            "source": "fallback",
        }
        try:
            if self._harvester and keywords:
                harvester_data = self._harvester.analyze_keywords(keywords[:5])
                if harvester_data:
                    trends["trending_topics"] = harvester_data.get("trends", [])
                    trends["source"] = "trend_harvester"
        except Exception as e:
            logger.warning(f"Trend harvester lookup failed: {e}")

        try:
            if self._collector:
                reddit_trends = self._collector.get_viral_trends(industry)
                if reddit_trends:
                    trends["viral_formats"].extend(reddit_trends[:5])
                    trends["source"] = trends["source"] + "+reddit"
        except Exception as e:
            logger.warning(f"Reddit trend collection failed: {e}")

        # Always include fallback viral formats
        if not trends["viral_formats"]:
            trends["viral_formats"] = self._get_fallback_formats(industry)

        return trends

    def get_trending_hashtags(self, industry: str, count: int = 10) -> List[str]:
        """Return relevant trending hashtags for an industry."""
        base_tags = {
            "roofing": ["#roofing", "#roofrepair", "#homeimprovement", "#contractor"],
            "restaurant": ["#foodie", "#eats", "#restaurant", "#foodphotography"],
            "fitness": ["#fitness", "#gym", "#workout", "#health"],
            "retail": ["#shopping", "#sale", "#fashion", "#style"],
            "tech": ["#tech", "#startup", "#innovation", "#software"],
            "realestate": ["#realestate", "#property", "#homes", "#realtor"],
        }
        industry_lower = industry.lower()
        for key, tags in base_tags.items():
            if key in industry_lower:
                return tags[:count]
        return [f"#{industry.replace(' ', '')}", "#marketing", "#business", "#growth"][:count]

    def _get_fallback_formats(self, industry: str) -> List[str]:
        return [
            "Before/After transformation reveal",
            "Day in the life behind the scenes",
            "Top 3 mistakes people make with...",
            "Customer success story spotlight",
            "Quick tip that saves time/money",
        ]

    def enhance_prompt_with_trends(self, base_prompt: str, industry: str, keywords: List[str] = None) -> str:
        """Inject trend context into an AI generation prompt."""
        try:
            trends = self.get_trends_for_industry(industry, keywords)
            trend_context = ""
            if trends["viral_formats"]:
                formats = ", ".join(trends["viral_formats"][:3])
                trend_context += f"\nCurrently viral content formats: {formats}."
            if trends["trending_topics"]:
                topics = ", ".join([t.get("keyword", str(t)) for t in trends["trending_topics"][:3]])
                trend_context += f"\nTrending topics: {topics}."
            if trend_context:
                return base_prompt + "\n\nTrend context (use to make content timely):" + trend_context
        except Exception as e:
            logger.warning(f"Prompt trend enhancement failed: {e}")
        return base_prompt
