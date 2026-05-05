"""
Competitor analysis module using Google Search API
Finds and analyzes actual competitors based on business data
"""

import logging
import requests
from typing import Dict, List, Any, Optional
import json

logger = logging.getLogger(__name__)

class CompetitorAnalyzer:
    """
    Analyzes competitors using Google Custom Search API
    Returns authentic competitor data only
    """
    
    def __init__(self, api_key: Optional[str] = None, engine_id: Optional[str] = None):
        self.api_key = api_key
        self.engine_id = engine_id
        self.base_url = "https://www.googleapis.com/customsearch/v1"
        
    def find_competitors(self, business_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Find top 5 competitors based on authentic business data
        """
        if not self.api_key or not self.engine_id:
            raise Exception("Google Search API credentials not configured")
            
        business_name = business_data['business_name']
        industry = business_data['industry']
        
        logger.info(f"Searching for competitors of {business_name} in {industry}")
        
        try:
            # Create targeted search queries
            search_queries = [
                f"{business_name} competitors",
                f"{business_name} alternatives",
                f"best {industry} companies like {business_name}",
                f"{industry} software alternatives to {business_name}"
            ]
            
            competitors = []
            seen_urls = set()
            
            for query in search_queries:
                if len(competitors) >= 5:
                    break
                    
                search_results = self._perform_search(query)
                
                for result in search_results.get('items', [])[:3]:
                    url = result.get('link', '')
                    
                    # Skip if we've seen this URL or if it's the original business
                    if url in seen_urls or business_data['domain'] in url:
                        continue
                        
                    competitor = {
                        'name': result.get('title', ''),
                        'url': url,
                        'description': result.get('snippet', ''),
                        'found_via': query,
                        'search_rank': len(competitors) + 1
                    }
                    
                    competitors.append(competitor)
                    seen_urls.add(url)
                    
                    if len(competitors) >= 5:
                        break
            
            logger.info(f"Found {len(competitors)} competitors for {business_name}")
            return competitors[:5]
            
        except Exception as e:
            logger.error(f"Competitor analysis failed: {e}")
            raise Exception(f"Failed to find competitors: {str(e)}")
    
    def _perform_search(self, query: str) -> Dict[str, Any]:
        """Perform Google Custom Search"""
        params = {
            'key': self.api_key,
            'cx': self.engine_id,
            'q': query,
            'num': 5
        }
        
        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Search API request failed: {e}")
            raise Exception(f"Search request failed: {str(e)}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse search response: {e}")
            raise Exception("Invalid search response format")
    
    def analyze_competitor_data(self, competitors: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze competitor data to extract insights
        """
        if not competitors:
            return {'total_competitors': 0, 'insights': []}
        
        analysis = {
            'total_competitors': len(competitors),
            'competitor_domains': [comp.get('url', '').split('/')[2] if comp.get('url') else '' for comp in competitors],
            'common_keywords': self._extract_common_keywords(competitors),
            'insights': self._generate_insights(competitors)
        }
        
        return analysis
    
    def _extract_common_keywords(self, competitors: List[Dict[str, Any]]) -> List[str]:
        """Extract common keywords from competitor descriptions"""
        all_text = ' '.join([comp.get('description', '') for comp in competitors])
        words = all_text.lower().split()
        
        # Filter for meaningful business keywords
        meaningful_words = [word for word in words if len(word) > 3 and word.isalpha()]
        
        # Count word frequency
        word_count = {}
        for word in meaningful_words:
            word_count[word] = word_count.get(word, 0) + 1
        
        # Return top keywords
        sorted_words = sorted(word_count.items(), key=lambda x: x[1], reverse=True)
        return [word for word, count in sorted_words[:10] if count > 1]
    
    def _generate_insights(self, competitors: List[Dict[str, Any]]) -> List[str]:
        """Generate competitive insights from competitor data"""
        insights = []
        
        if len(competitors) > 3:
            insights.append(f"High competition detected with {len(competitors)} direct competitors")
        elif len(competitors) < 2:
            insights.append("Limited direct competition - potential market opportunity")
        
        # Analyze competitor names for patterns
        competitor_names = [comp.get('name', '') for comp in competitors]
        if any('Inc' in name or 'LLC' in name for name in competitor_names):
            insights.append("Established corporate competitors present")
        
        # Analyze descriptions for service patterns
        descriptions = ' '.join([comp.get('description', '') for comp in competitors])
        if 'software' in descriptions.lower():
            insights.append("Software-focused competitive landscape")
        if 'solution' in descriptions.lower():
            insights.append("Solution-oriented market positioning common")
        
        return insights