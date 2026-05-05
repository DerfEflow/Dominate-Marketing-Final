"""
Google Ads API Client - Money-weighted demand analysis via Keyword Planner
Implements the core demand discovery protocol with CPC and competition signals
"""

import os
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

class GoogleAdsClient:
    """
    Google Ads API client for keyword planning and demand analysis
    Provides money-weighted demand signals via CPC and competition data
    """
    
    def __init__(self):
        # Google Ads API requires OAuth2 or service account
        self.customer_id = os.environ.get('GOOGLE_ADS_CUSTOMER_ID')
        self.developer_token = os.environ.get('GOOGLE_ADS_DEVELOPER_TOKEN')
        self.client_id = os.environ.get('GOOGLE_ADS_CLIENT_ID')
        self.client_secret = os.environ.get('GOOGLE_ADS_CLIENT_SECRET')
        self.refresh_token = os.environ.get('GOOGLE_ADS_REFRESH_TOKEN')
        
        if not all([self.customer_id, self.developer_token, self.client_id, self.client_secret, self.refresh_token]):
            logging.error("Google Ads API credentials incomplete")
    
    def validate_credentials(self) -> bool:
        """Check if all required Google Ads API credentials are present"""
        return all([
            self.customer_id,
            self.developer_token, 
            self.client_id,
            self.client_secret,
            self.refresh_token
        ])
    
    async def get_keyword_ideas(self, seed_keywords: List[str], geo_location: str) -> List[Dict[str, Any]]:
        """
        Get keyword ideas with CPC and competition data using Keyword Plan Idea Service
        Returns money-weighted demand signals
        """
        if not self.validate_credentials():
            raise ValueError("Google Ads API credentials required for keyword planning")
        
        try:
            # Import Google Ads API components
            from google.ads.googleads import client as GoogleAdsClientModule
            from google.ads.googleads.v16.enums.types import keyword_plan_network
            
            # Initialize client
            config = {
                'developer_token': self.developer_token,
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'refresh_token': self.refresh_token,
                'use_proto_plus': True
            }
            
            client = GoogleAdsClientModule.GoogleAdsClient.load_from_dict(config)
            keyword_plan_idea_service = client.get_service("KeywordPlanIdeaService")
            
            # Build request
            request = client.get_type("GenerateKeywordIdeasRequest")
            request.customer_id = self.customer_id
            
            # Set seed keywords
            request.keyword_seed.keywords.extend(seed_keywords)
            
            # Set location and language targeting
            geo_target = client.get_type("LocationInfo")
            if geo_location.upper() == 'US':
                geo_target.geo_target_constant = "geoTargetConstants/2840"  # US
            elif geo_location.upper() == 'CA':
                geo_target.geo_target_constant = "geoTargetConstants/2124"  # Canada
            elif geo_location.upper() == 'GB':
                geo_target.geo_target_constant = "geoTargetConstants/2826"  # UK
            else:
                geo_target.geo_target_constant = "geoTargetConstants/2840"  # Default to US
            
            request.geo_target_constants.append(geo_target.geo_target_constant)
            
            # Set language
            language = client.get_type("LanguageInfo")
            language.language_constant = "languageConstants/1000"  # English
            request.language = language
            
            # Set network
            request.keyword_plan_network = keyword_plan_network.KeywordPlanNetworkEnum.GOOGLE_SEARCH
            
            # Execute request
            response = keyword_plan_idea_service.generate_keyword_ideas(request=request)
            
            keyword_ideas = []
            for idea in response.results:
                keyword_data = {
                    'keyword': idea.text,
                    'avg_monthly_searches': idea.keyword_idea_metrics.avg_monthly_searches,
                    'competition': idea.keyword_idea_metrics.competition.name,
                    'competition_index': idea.keyword_idea_metrics.competition_index,
                    'low_top_of_page_bid_micros': idea.keyword_idea_metrics.low_top_of_page_bid_micros,
                    'high_top_of_page_bid_micros': idea.keyword_idea_metrics.high_top_of_page_bid_micros,
                    'cpc_low': idea.keyword_idea_metrics.low_top_of_page_bid_micros / 1_000_000 if idea.keyword_idea_metrics.low_top_of_page_bid_micros else 0,
                    'cpc_high': idea.keyword_idea_metrics.high_top_of_page_bid_micros / 1_000_000 if idea.keyword_idea_metrics.high_top_of_page_bid_micros else 0,
                    'money_weighted_score': self._calculate_money_weight(
                        idea.keyword_idea_metrics.avg_monthly_searches,
                        idea.keyword_idea_metrics.high_top_of_page_bid_micros / 1_000_000 if idea.keyword_idea_metrics.high_top_of_page_bid_micros else 0,
                        idea.keyword_idea_metrics.competition_index
                    ),
                    'discovery_method': 'google_ads_keyword_planner'
                }
                keyword_ideas.append(keyword_data)
            
            # Sort by money-weighted score
            keyword_ideas.sort(key=lambda x: x['money_weighted_score'], reverse=True)
            
            return keyword_ideas[:50]  # Return top 50
            
        except ImportError:
            raise ValueError("Google Ads API library not installed. Run: pip install google-ads")
        except Exception as e:
            logging.error(f"Google Ads API error: {e}")
            raise
    
    def _calculate_money_weight(self, search_volume: int, cpc: float, competition_index: float) -> float:
        """
        Calculate money-weighted demand score
        Higher CPC + Higher Volume + Reasonable Competition = Higher Score
        """
        if not search_volume or search_volume <= 0:
            return 0
        
        # Normalize competition (0-100 scale, prefer moderate competition)
        competition_factor = 1.0
        if competition_index:
            # Sweet spot around 30-70 competition index
            if 30 <= competition_index <= 70:
                competition_factor = 1.2
            elif competition_index > 70:
                competition_factor = 0.8  # Too competitive
            else:
                competition_factor = 1.0  # Low competition
        
        # Volume score (log scale to prevent huge keywords from dominating)
        import math
        volume_score = math.log10(search_volume + 1)
        
        # CPC score (linear, but cap at reasonable levels)
        cpc_score = min(cpc, 50.0)  # Cap at $50 CPC
        
        # Combined score
        money_weight = (volume_score * cpc_score * competition_factor)
        
        return round(money_weight, 2)
    
    async def get_traffic_estimates(self, keywords: List[str], geo_location: str) -> Dict[str, Any]:
        """
        Get traffic estimates for specific keywords
        """
        if not self.validate_credentials():
            raise ValueError("Google Ads API credentials required")
        
        try:
            # This would use the Traffic Estimator service
            # Implementation would follow similar pattern to keyword ideas
            estimates = {
                'total_impressions': 0,
                'total_clicks': 0,
                'average_cpc': 0.0,
                'keywords': []
            }
            
            # For each keyword, get individual estimates
            for keyword in keywords:
                # Would call Traffic Estimator API here
                keyword_estimate = {
                    'keyword': keyword,
                    'impressions': 0,
                    'clicks': 0,
                    'cpc': 0.0,
                    'position': 0.0
                }
                estimates['keywords'].append(keyword_estimate)
            
            return estimates
            
        except Exception as e:
            logging.error(f"Traffic estimation error: {e}")
            raise
    
    def get_required_credentials_info(self) -> Dict[str, str]:
        """
        Return information about required Google Ads API credentials
        """
        return {
            'GOOGLE_ADS_CUSTOMER_ID': 'Your Google Ads customer ID (10-digit number)',
            'GOOGLE_ADS_DEVELOPER_TOKEN': 'Developer token from Google Ads API center',
            'GOOGLE_ADS_CLIENT_ID': 'OAuth2 client ID from Google Cloud Console',
            'GOOGLE_ADS_CLIENT_SECRET': 'OAuth2 client secret from Google Cloud Console',
            'GOOGLE_ADS_REFRESH_TOKEN': 'OAuth2 refresh token for your account',
            'setup_instructions': 'https://developers.google.com/google-ads/api/docs/first-call/overview'
        }