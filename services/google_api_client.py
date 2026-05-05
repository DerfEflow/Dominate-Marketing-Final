"""
Google API client - wraps Google Places, Search Console, and custom search APIs.
"""
import logging
import os
import requests

logger = logging.getLogger(__name__)

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")


class GoogleAPIClient:
    def __init__(self):
        self.api_key = GOOGLE_API_KEY
        self.places_base = "https://maps.googleapis.com/maps/api/place"
        self.custom_search_base = "https://www.googleapis.com/customsearch/v1"

    def search_businesses(self, query: str, location: str = "", radius: int = 50000) -> list:
        """Search for businesses using Google Places API."""
        if not self.api_key:
            logger.warning("No Google API key configured")
            return []
        try:
            params = {
                "query": f"{query} {location}".strip(),
                "key": self.api_key,
            }
            resp = requests.get(f"{self.places_base}/textsearch/json", params=params, timeout=10)
            data = resp.json()
            return data.get("results", [])
        except Exception as e:
            logger.error(f"Google Places search failed: {e}")
            return []

    def get_place_details(self, place_id: str) -> dict:
        """Get details for a specific place."""
        if not self.api_key:
            return {}
        try:
            params = {
                "place_id": place_id,
                "fields": "name,rating,user_ratings_total,website,formatted_phone_number,formatted_address",
                "key": self.api_key,
            }
            resp = requests.get(f"{self.places_base}/details/json", params=params, timeout=10)
            data = resp.json()
            return data.get("result", {})
        except Exception as e:
            logger.error(f"Google Place details failed: {e}")
            return {}

    def custom_search(self, query: str, num: int = 5) -> list:
        """Run a Google Custom Search."""
        cx = os.environ.get("GOOGLE_CUSTOM_SEARCH_CX", "")
        if not self.api_key or not cx:
            return []
        try:
            params = {"key": self.api_key, "cx": cx, "q": query, "num": min(num, 10)}
            resp = requests.get(self.custom_search_base, params=params, timeout=10)
            data = resp.json()
            return data.get("items", [])
        except Exception as e:
            logger.error(f"Google Custom Search failed: {e}")
            return []
