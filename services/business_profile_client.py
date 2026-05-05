"""
Google Business Profile API Client - Competitive insights and local performance
Analyzes business profiles, reviews, and local ranking factors
"""

import os
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import requests
import asyncio

class BusinessProfileClient:
    """
    Google Business Profile API client for competitive analysis and local insights
    Provides review analysis, performance metrics, and competitive intelligence
    """
    
    def __init__(self):
        self.api_key = os.environ.get('GOOGLE_BUSINESS_PROFILE_API_KEY')
        self.base_url = "https://mybusinessbusinessinformation.googleapis.com/v1"
        self.performance_url = "https://mybusinessaccountmanagement.googleapis.com/v1"
        
        # OAuth credentials
        self.client_id = os.environ.get('GOOGLE_OAUTH_CLIENT_ID')
        self.client_secret = os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET')
        self.refresh_token = os.environ.get('GOOGLE_BUSINESS_PROFILE_REFRESH_TOKEN')
    
    def validate_credentials(self) -> bool:
        """Check if Business Profile API credentials are available"""
        return bool(self.client_id and self.client_secret and self.refresh_token)
    
    async def get_access_token(self) -> str:
        """Get OAuth2 access token for Business Profile API"""
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
            logging.error(f"Failed to get Business Profile access token: {e}")
            raise
    
    async def get_business_insights(self, location_name: str) -> Dict[str, Any]:
        """
        Get insights for a business location including views, actions, and search queries
        """
        if not self.validate_credentials():
            raise ValueError("Business Profile OAuth credentials required")
        
        try:
            access_token = await self.get_access_token()
            headers = {'Authorization': f'Bearer {access_token}'}
            
            # Get basic insights
            insights_url = f"{self.performance_url}/{location_name}/insights:search"
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=90)
            
            request_body = {
                'startDate': start_date.strftime('%Y-%m-%d'),
                'endDate': end_date.strftime('%Y-%m-%d'),
                'basic_insights': {
                    'metric_requests': [
                        {'metric': 'VIEWS'},
                        {'metric': 'ACTIONS'},
                        {'metric': 'PHONE_CALLS'},
                        {'metric': 'DIRECTION_REQUESTS'},
                        {'metric': 'WEBSITE_CLICKS'}
                    ]
                }
            }
            
            response = requests.post(insights_url, headers=headers, json=request_body, timeout=15)
            response.raise_for_status()
            
            insights_data = response.json()
            
            # Get search query insights
            search_insights = await self._get_search_query_insights(location_name, access_token)
            
            return {
                'basic_insights': insights_data,
                'search_insights': search_insights,
                'analysis_period': {
                    'start_date': start_date.strftime('%Y-%m-%d'),
                    'end_date': end_date.strftime('%Y-%m-%d')
                },
                'discovery_method': 'business_profile_api'
            }
            
        except Exception as e:
            logging.error(f"Business insights error: {e}")
            raise
    
    async def _get_search_query_insights(self, location_name: str, access_token: str) -> Dict[str, Any]:
        """
        Get search query insights to understand how customers find the business
        """
        try:
            headers = {'Authorization': f'Bearer {access_token}'}
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            request_body = {
                'startDate': start_date.strftime('%Y-%m-%d'),
                'endDate': end_date.strftime('%Y-%m-%d'),
                'search_query_insights': {
                    'metric_requests': [
                        {'metric': 'QUERIES_DIRECT'},
                        {'metric': 'QUERIES_INDIRECT'},
                        {'metric': 'QUERIES_CHAIN'}
                    ]
                }
            }
            
            url = f"{self.performance_url}/{location_name}/insights:search"
            response = requests.post(url, headers=headers, json=request_body, timeout=15)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logging.warning(f"Search query insights failed: {e}")
            return {}
    
    async def analyze_competitor_profiles(self, business_type: str, location: str, radius_km: int = 25) -> List[Dict[str, Any]]:
        """
        Analyze competitor business profiles in the area
        Note: This requires the Places API as Business Profile API only accesses owned locations
        """
        # This would integrate with Places API for competitor discovery
        # then use Business Profile API for owned location analysis
        
        try:
            # Use Google Places API to find competitors
            from services.google_api_client import GoogleAPIClient
            places_client = GoogleAPIClient()
            
            competitors = await places_client.find_local_businesses(business_type, location, radius_km * 1000)
            
            competitor_analysis = []
            
            for competitor in competitors:
                # Analyze each competitor's public profile
                analysis = await self._analyze_competitor_profile(competitor)
                competitor_analysis.append(analysis)
                
                # Rate limiting
                await asyncio.sleep(0.5)
            
            return competitor_analysis
            
        except Exception as e:
            logging.error(f"Competitor profile analysis error: {e}")
            return []
    
    async def _analyze_competitor_profile(self, competitor: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a single competitor's business profile
        """
        try:
            analysis = {
                'name': competitor.get('name'),
                'place_id': competitor.get('place_id'),
                'rating': competitor.get('rating', 0),
                'review_count': competitor.get('user_ratings_total', 0),
                'price_level': competitor.get('price_level'),
                'business_status': competitor.get('business_status'),
                'types': competitor.get('types', []),
                'vicinity': competitor.get('vicinity'),
            }
            
            # Analyze review themes if available
            if competitor.get('place_id'):
                review_analysis = await self._analyze_competitor_reviews(competitor['place_id'])
                analysis['review_analysis'] = review_analysis
            
            # Calculate competitive strength score
            analysis['competitive_strength'] = self._calculate_competitive_strength(analysis)
            
            return analysis
            
        except Exception as e:
            logging.warning(f"Individual competitor analysis failed: {e}")
            return {'error': str(e)}
    
    async def _analyze_competitor_reviews(self, place_id: str) -> Dict[str, Any]:
        """
        Analyze competitor reviews for sentiment and themes
        """
        try:
            # This would use Google Places API to get reviews
            # then Natural Language API for sentiment analysis
            
            from services.google_api_client import GoogleAPIClient
            places_client = GoogleAPIClient()
            
            reviews = await places_client.get_place_reviews(place_id)
            
            if not reviews:
                return {'error': 'No reviews available'}
            
            # Analyze review sentiment and extract themes
            positive_themes = []
            negative_themes = []
            
            for review in reviews:
                if review.get('rating', 0) >= 4:
                    positive_themes.extend(self._extract_review_themes(review.get('text', '')))
                elif review.get('rating', 0) <= 2:
                    negative_themes.extend(self._extract_review_themes(review.get('text', '')))
            
            return {
                'total_reviews': len(reviews),
                'positive_themes': self._get_common_themes(positive_themes),
                'negative_themes': self._get_common_themes(negative_themes),
                'avg_rating': sum(r.get('rating', 0) for r in reviews) / len(reviews) if reviews else 0
            }
            
        except Exception as e:
            logging.warning(f"Review analysis failed: {e}")
            return {'error': str(e)}
    
    def _extract_review_themes(self, review_text: str) -> List[str]:
        """
        Extract themes from review text using keyword matching
        """
        themes = []
        review_lower = review_text.lower()
        
        # Common business themes to look for
        theme_keywords = {
            'service_quality': ['service', 'quality', 'professional', 'excellent', 'amazing'],
            'pricing': ['price', 'cost', 'expensive', 'cheap', 'affordable', 'value'],
            'speed': ['fast', 'quick', 'slow', 'timely', 'prompt', 'delay'],
            'staff': ['staff', 'employee', 'friendly', 'rude', 'helpful', 'knowledgeable'],
            'location': ['location', 'parking', 'convenient', 'accessible'],
            'communication': ['communication', 'responsive', 'contact', 'follow-up']
        }
        
        for theme, keywords in theme_keywords.items():
            if any(keyword in review_lower for keyword in keywords):
                themes.append(theme)
        
        return themes
    
    def _get_common_themes(self, themes: List[str]) -> List[Dict[str, Any]]:
        """
        Get most common themes from list
        """
        from collections import Counter
        theme_counts = Counter(themes)
        
        return [
            {'theme': theme, 'count': count}
            for theme, count in theme_counts.most_common(5)
        ]
    
    def _calculate_competitive_strength(self, profile: Dict[str, Any]) -> float:
        """
        Calculate competitive strength score based on profile metrics
        """
        score = 0
        
        # Rating factor (0-5 scale)
        rating = profile.get('rating', 0)
        score += (rating / 5.0) * 30
        
        # Review volume factor (log scale)
        review_count = profile.get('review_count', 0)
        if review_count > 0:
            import math
            score += min(math.log10(review_count + 1) * 10, 25)
        
        # Business status factor
        if profile.get('business_status') == 'OPERATIONAL':
            score += 15
        
        # Price level factor (having pricing info is good)
        if profile.get('price_level'):
            score += 10
        
        # Business types diversity
        types_count = len(profile.get('types', []))
        score += min(types_count * 2, 20)
        
        return round(score, 1)
    
    async def get_location_performance_comparison(self, location_name: str, competitor_locations: List[str]) -> Dict[str, Any]:
        """
        Compare performance metrics between owned location and competitors
        """
        if not self.validate_credentials():
            raise ValueError("Business Profile OAuth credentials required")
        
        try:
            # Get own performance
            own_insights = await self.get_business_insights(location_name)
            
            # Get competitor data (limited by what's publicly available)
            competitor_comparisons = []
            
            for comp_location in competitor_locations:
                try:
                    comp_data = await self._get_public_competitor_data(comp_location)
                    competitor_comparisons.append(comp_data)
                except Exception as e:
                    logging.warning(f"Failed to get competitor data for {comp_location}: {e}")
            
            return {
                'own_performance': own_insights,
                'competitor_comparison': competitor_comparisons,
                'market_position': self._calculate_market_position(own_insights, competitor_comparisons)
            }
            
        except Exception as e:
            logging.error(f"Performance comparison error: {e}")
            raise
    
    async def _get_public_competitor_data(self, location_identifier: str) -> Dict[str, Any]:
        """
        Get publicly available competitor data
        """
        # This would use Places API to get public information
        return {
            'location': location_identifier,
            'public_metrics': 'limited',
            'note': 'Only public data available for competitors'
        }
    
    def _calculate_market_position(self, own_data: Dict[str, Any], competitor_data: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        Calculate market position relative to competitors
        """
        return {
            'position': 'analysis_requires_full_implementation',
            'insights': 'Market position analysis based on available metrics'
        }
    
    def get_required_credentials_info(self) -> Dict[str, str]:
        """
        Return information about required Business Profile API credentials
        """
        return {
            'GOOGLE_OAUTH_CLIENT_ID': 'OAuth2 client ID with Business Profile API access',
            'GOOGLE_OAUTH_CLIENT_SECRET': 'OAuth2 client secret',
            'GOOGLE_BUSINESS_PROFILE_REFRESH_TOKEN': 'Refresh token for Business Profile access',
            'scopes_required': [
                'https://www.googleapis.com/auth/business.manage',
                'https://www.googleapis.com/auth/business.read'
            ],
            'setup_instructions': 'https://developers.google.com/my-business/content/overview'
        }