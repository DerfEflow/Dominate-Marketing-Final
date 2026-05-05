"""
Google Search Console API Client - "Striking Distance" keyword analysis
Finds keywords where your site already has impressions but could rank better
"""

import os
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import requests

class SearchConsoleClient:
    """
    Google Search Console API client for finding "striking distance" opportunities
    Analyzes existing impressions by geo to identify quick win keywords
    """
    
    def __init__(self):
        self.api_key = os.environ.get('GOOGLE_SEARCH_CONSOLE_API_KEY')
        self.base_url = "https://searchconsole.googleapis.com/webmasters/v3"
        
        # OAuth credentials for Search Console
        self.client_id = os.environ.get('GOOGLE_OAUTH_CLIENT_ID')
        self.client_secret = os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET') 
        self.refresh_token = os.environ.get('GOOGLE_SEARCH_CONSOLE_REFRESH_TOKEN')
        
    def validate_credentials(self) -> bool:
        """Check if Search Console API credentials are available"""
        return bool(self.client_id and self.client_secret and self.refresh_token)
    
    async def get_access_token(self) -> Optional[str]:
        """Get OAuth2 access token for Search Console API"""
        try:
            token_url = "https://oauth2.googleapis.com/token"
            data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'refresh_token': self.refresh_token,
                'grant_type': 'refresh_token'
            }
            
            response = requests.post(token_url, data=data, timeout=10)
            response.raise_for_status()
            
            return response.json()['access_token']
            
        except Exception as e:
            logging.error(f"Failed to get Search Console access token: {e}")
            raise
    
    async def get_site_properties(self) -> List[str]:
        """Get list of verified properties in Search Console"""
        if not self.validate_credentials():
            raise ValueError("Search Console OAuth credentials required")
        
        try:
            access_token = await self.get_access_token()
            headers = {'Authorization': f'Bearer {access_token}'}
            
            response = requests.get(f"{self.base_url}/sites", headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            return [site['siteUrl'] for site in data.get('siteEntry', [])]
            
        except Exception as e:
            logging.error(f"Failed to get site properties: {e}")
            return []
    
    async def analyze_striking_distance_keywords(self, site_url: str, geo_filter: str = None) -> List[Dict[str, Any]]:
        """
        Find "striking distance" keywords - queries with impressions but low CTR/position
        These represent quick win opportunities for content optimization
        """
        if not self.validate_credentials():
            raise ValueError("Search Console OAuth credentials required")
        
        try:
            access_token = await self.get_access_token()
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            # Query for last 90 days
            end_date = datetime.now()
            start_date = end_date - timedelta(days=90)
            
            request_body = {
                'startDate': start_date.strftime('%Y-%m-%d'),
                'endDate': end_date.strftime('%Y-%m-%d'),
                'dimensions': ['query', 'country', 'page'],
                'rowLimit': 1000,
                'startRow': 0
            }
            
            # Add geo filter if specified
            if geo_filter:
                request_body['dimensionFilterGroups'] = [{
                    'filters': [{
                        'dimension': 'country',
                        'operator': 'equals',
                        'expression': geo_filter
                    }]
                }]
            
            url = f"{self.base_url}/sites/{site_url}/searchAnalytics/query"
            response = requests.post(url, headers=headers, json=request_body, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            striking_distance = []
            
            for row in data.get('rows', []):
                query = row['keys'][0]
                country = row['keys'][1] if len(row['keys']) > 1 else 'unknown'
                page = row['keys'][2] if len(row['keys']) > 2 else 'unknown'
                
                clicks = row['clicks']
                impressions = row['impressions']
                ctr = row['ctr']
                position = row['position']
                
                # Identify striking distance opportunities
                # Criteria: impressions > 50, position 8-20, CTR < 5%
                if (impressions >= 50 and 
                    8 <= position <= 20 and 
                    ctr < 0.05):
                    
                    opportunity_score = self._calculate_opportunity_score(
                        impressions, position, ctr, clicks
                    )
                    
                    keyword_data = {
                        'query': query,
                        'country': country,
                        'landing_page': page,
                        'current_position': position,
                        'impressions': impressions,
                        'clicks': clicks,
                        'ctr': ctr,
                        'opportunity_score': opportunity_score,
                        'potential_clicks': self._estimate_potential_clicks(impressions, position),
                        'optimization_type': self._suggest_optimization_type(position, ctr),
                        'discovery_method': 'search_console_striking_distance'
                    }
                    striking_distance.append(keyword_data)
            
            # Sort by opportunity score
            striking_distance.sort(key=lambda x: x['opportunity_score'], reverse=True)
            
            return striking_distance[:50]  # Top 50 opportunities
            
        except Exception as e:
            logging.error(f"Search Console analysis error: {e}")
            raise
    
    def _calculate_opportunity_score(self, impressions: int, position: float, ctr: float, clicks: int) -> float:
        """
        Calculate opportunity score for striking distance keywords
        Higher impressions + worse position + low CTR = higher opportunity
        """
        # Base score from impression volume
        volume_score = min(impressions / 1000, 10)  # Cap at 10
        
        # Position penalty (worse position = higher opportunity)
        position_score = max(0, (20 - position) / 2)
        
        # CTR opportunity (lower CTR = higher opportunity) 
        ctr_opportunity = max(0, (0.05 - ctr) * 100)
        
        # Current performance factor
        performance_factor = 1 + (clicks / max(impressions, 1))
        
        opportunity = (volume_score + position_score + ctr_opportunity) * performance_factor
        
        return round(opportunity, 2)
    
    def _estimate_potential_clicks(self, impressions: int, current_position: float) -> int:
        """
        Estimate potential clicks if ranking improved to position 3-5
        """
        # Average CTR by position (industry benchmarks)
        ctr_by_position = {
            1: 0.28, 2: 0.15, 3: 0.11, 4: 0.08, 5: 0.06,
            6: 0.05, 7: 0.04, 8: 0.03, 9: 0.03, 10: 0.02
        }
        
        # Estimate CTR if we rank position 3-5
        target_position = 4
        target_ctr = ctr_by_position.get(target_position, 0.08)
        
        return int(impressions * target_ctr)
    
    def _suggest_optimization_type(self, position: float, ctr: float) -> str:
        """
        Suggest optimization approach based on current metrics
        """
        if position > 15:
            return "content_expansion"  # Need more content depth
        elif position > 10:
            return "technical_seo"  # Need technical improvements
        elif ctr < 0.02:
            return "title_meta_optimization"  # Need better snippets
        else:
            return "content_quality"  # Need better content alignment
    
    async def get_top_pages_by_country(self, site_url: str, country: str = None) -> List[Dict[str, Any]]:
        """
        Get top performing pages by country for content analysis
        """
        if not self.validate_credentials():
            raise ValueError("Search Console OAuth credentials required")
        
        try:
            access_token = await self.get_access_token()
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            request_body = {
                'startDate': start_date.strftime('%Y-%m-%d'),
                'endDate': end_date.strftime('%Y-%m-%d'),
                'dimensions': ['page'],
                'rowLimit': 100
            }
            
            if country:
                request_body['dimensionFilterGroups'] = [{
                    'filters': [{
                        'dimension': 'country',
                        'operator': 'equals', 
                        'expression': country
                    }]
                }]
            
            url = f"{self.base_url}/sites/{site_url}/searchAnalytics/query"
            response = requests.post(url, headers=headers, json=request_body, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            pages = []
            
            for row in data.get('rows', []):
                page_data = {
                    'page': row['keys'][0],
                    'clicks': row['clicks'],
                    'impressions': row['impressions'],
                    'ctr': row['ctr'],
                    'position': row['position']
                }
                pages.append(page_data)
            
            return pages
            
        except Exception as e:
            logging.error(f"Top pages analysis error: {e}")
            return []
    
    def get_required_credentials_info(self) -> Dict[str, str]:
        """
        Return information about required Search Console API credentials
        """
        return {
            'GOOGLE_OAUTH_CLIENT_ID': 'OAuth2 client ID with Search Console API access',
            'GOOGLE_OAUTH_CLIENT_SECRET': 'OAuth2 client secret',
            'GOOGLE_SEARCH_CONSOLE_REFRESH_TOKEN': 'Refresh token for Search Console access',
            'scope_required': 'https://www.googleapis.com/auth/webmasters.readonly',
            'setup_instructions': 'https://developers.google.com/webmaster-tools/search-console-api/v3/quickstart'
        }