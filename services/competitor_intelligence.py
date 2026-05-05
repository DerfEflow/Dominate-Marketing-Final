"""
Competitor Intelligence Service - Enhanced competitor discovery and analysis
"""

import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional
import requests
from bs4 import BeautifulSoup
from services.google_api_client import GoogleAPIClient

class CompetitorIntelligence:
    """
    Enhanced competitor intelligence gathering following the comprehensive protocol
    """
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.google_client = GoogleAPIClient()
    
    async def discover_competitors(self, business_url: str, geo_location: str = 'US', 
                                 industry: Optional[str] = None) -> Dict[str, Any]:
        """
        Discover competitors using multiple methods
        """
        try:
            competitor_data = {
                'discovery_timestamp': datetime.utcnow().isoformat(),
                'source_url': business_url,
                'geo_location': geo_location,
                'industry': industry,
                'discovery_methods': []
            }
            
            # Method 1: Search-based competitor discovery
            search_competitors = await self._discover_via_search(business_url, geo_location, industry)
            competitor_data['search_discovered'] = search_competitors
            competitor_data['discovery_methods'].append('search_analysis')
            
            # Method 2: Industry directory analysis
            directory_competitors = await self._discover_via_directories(geo_location, industry)
            competitor_data['directory_discovered'] = directory_competitors
            competitor_data['discovery_methods'].append('directory_analysis')
            
            # Method 3: Social media competitor discovery
            social_competitors = await self._discover_via_social(business_url, industry)
            competitor_data['social_discovered'] = social_competitors
            competitor_data['discovery_methods'].append('social_monitoring')
            
            # Consolidate and rank competitors
            all_competitors = self._consolidate_competitors(
                search_competitors, directory_competitors, social_competitors
            )
            
            competitor_data['direct_competitors'] = all_competitors.get('direct', [])
            competitor_data['indirect_competitors'] = all_competitors.get('indirect', [])
            competitor_data['market_leaders'] = all_competitors.get('leaders', [])
            competitor_data['local_players'] = all_competitors.get('local', [])
            
            return competitor_data
            
        except Exception as e:
            logging.error(f"Competitor discovery failed: {e}")
            return {'error': str(e)}
    
    async def _discover_via_search(self, business_url: str, geo_location: str, 
                                 industry: Optional[str]) -> List[Dict[str, Any]]:
        """
        Discover competitors through real search analysis using Google Custom Search API
        """
        competitors = []
        
        try:
            # Extract business keywords from URL and industry
            search_terms = self._generate_search_terms(business_url, industry, geo_location)
            
            for term in search_terms[:3]:  # Limit searches to avoid quota issues
                try:
                    # Use real Google Custom Search API
                    search_results = await self.google_client.search_competitors(term, geo_location, 10)
                    
                    for i, result in enumerate(search_results):
                        competitor = {
                            'name': result.get('name', 'Unknown'),
                            'url': result.get('url', ''),
                            'discovery_method': 'custom_search_api',
                            'search_term': term,
                            'ranking_position': i + 1,
                            'description': result.get('description', ''),
                            'display_link': result.get('display_link', ''),
                            'local_presence': self._assess_local_presence_from_search(result, geo_location)
                        }
                        competitors.append(competitor)
                        
                    await asyncio.sleep(0.5)  # Rate limiting
                    
                except Exception as e:
                    logging.warning(f"Search discovery failed for term {term}: {e}")
                    continue
            
            return competitors[:15]  # Limit to top 15
            
        except Exception as e:
            logging.error(f"Search-based discovery failed: {e}")
            return []
    
    async def _discover_via_directories(self, geo_location: str, 
                                      industry: Optional[str]) -> List[Dict[str, Any]]:
        """
        Discover competitors through Google Places API (real directory data)
        """
        competitors = []
        
        try:
            # Convert geo_location to coordinates for Places API
            location_coords = self._get_location_coordinates(geo_location)
            
            if not location_coords:
                logging.warning(f"Could not get coordinates for {geo_location}")
                return []
            
            # Use Google Places API for real business discovery
            business_type = industry or 'business'
            places_results = await self.google_client.find_local_businesses(
                business_type, location_coords, radius=50000
            )
            
            for result in places_results:
                competitor = {
                    'name': result.get('name', 'Unknown Business'),
                    'url': result.get('website'),
                    'phone': result.get('phone'),
                    'address': result.get('vicinity', ''),
                    'rating': result.get('rating', 0),
                    'review_count': result.get('user_ratings_total', 0),
                    'discovery_method': 'google_places_api',
                    'directory_source': 'google_places',
                    'business_category': ', '.join(result.get('types', [])),
                    'price_level': result.get('price_level'),
                    'place_id': result.get('place_id'),
                    'business_status': result.get('business_status', 'OPERATIONAL'),
                    'opening_hours': result.get('opening_hours', []),
                    'google_url': result.get('google_url'),
                    'reviews': result.get('reviews', [])
                }
                competitors.append(competitor)
            
            return competitors[:20]  # Google Places provides quality data
            
        except Exception as e:
            logging.error(f"Places API discovery failed: {e}")
            return []
    
    async def _discover_via_social(self, business_url: str, 
                                 industry: Optional[str]) -> List[Dict[str, Any]]:
        """
        Discover competitors through real YouTube API analysis
        """
        competitors = []
        
        try:
            # Focus on YouTube as it provides the most accessible API
            search_terms = self._generate_social_search_terms(business_url, industry)
            
            for term in search_terms[:2]:  # Limit to avoid quota issues
                try:
                    # Use real YouTube API
                    youtube_results = await self.google_client.search_youtube_competitors(term, 8)
                    
                    for result in youtube_results:
                        competitor = {
                            'name': result.get('title', 'Unknown Channel'),
                            'social_handle': result.get('custom_url', ''),
                            'platform': 'youtube',
                            'channel_id': result.get('channel_id'),
                            'followers': result.get('subscriber_count', 0),
                            'video_count': result.get('video_count', 0),
                            'total_views': result.get('view_count', 0),
                            'discovery_method': 'youtube_api',
                            'description': result.get('description', ''),
                            'country': result.get('country', ''),
                            'published_at': result.get('published_at', ''),
                            'thumbnail': result.get('thumbnail', '')
                        }
                        competitors.append(competitor)
                        
                    await asyncio.sleep(0.5)  # Rate limiting
                    
                except Exception as e:
                    logging.warning(f"YouTube discovery failed for term {term}: {e}")
                    continue
            
            return competitors[:15]  # Limit results
            
        except Exception as e:
            logging.error(f"Social media discovery failed: {e}")
            return []
    
    def _generate_search_terms(self, business_url: str, industry: Optional[str], 
                             geo_location: str) -> List[str]:
        """Generate search terms for competitor discovery"""
        terms = []
        
        # Extract domain keywords
        domain_parts = business_url.replace('https://', '').replace('http://', '').split('.')[0]
        
        # Industry-based terms
        if industry:
            terms.extend([
                f"{industry} {geo_location}",
                f"best {industry} near me",
                f"{industry} services {geo_location}"
            ])
        
        # Generic terms
        terms.extend([
            f"local services {geo_location}",
            f"contractors {geo_location}",
            f"home services {geo_location}"
        ])
        
        return terms
    
    async def _simulate_search_results(self, term: str, geo_location: str) -> List[Dict[str, Any]]:
        """Simulate search results for competitor discovery"""
        # This would integrate with real search APIs in production
        simulated_results = [
            {
                'name': f'{term.split()[0].title()} Pro Services',
                'url': f'https://{term.split()[0].lower()}pro.com',
                'position': 1,
                'description': f'Professional {term} services in {geo_location}',
                'local_indicators': ['phone', 'address', 'hours']
            },
            {
                'name': f'{geo_location} {term.split()[0].title()} Experts',
                'url': f'https://{geo_location.lower()}{term.split()[0].lower()}.com',
                'position': 2,
                'description': f'Local {term} specialists serving {geo_location}',
                'local_indicators': ['phone', 'address', 'reviews']
            },
            {
                'name': f'Elite {term.split()[0].title()} Solutions',
                'url': f'https://elite{term.split()[0].lower()}.com',
                'position': 3,
                'description': f'Premium {term} services with guaranteed results',
                'local_indicators': ['phone', 'reviews']
            }
        ]
        
        return simulated_results
    
    async def _simulate_directory_results(self, source: str, geo_location: str, 
                                        industry: Optional[str]) -> List[Dict[str, Any]]:
        """Simulate directory search results"""
        base_names = ['Pro', 'Expert', 'Elite', 'Premium', 'Quality', 'Reliable', 'Trusted']
        service_types = [industry or 'Services', 'Solutions', 'Contractors', 'Specialists']
        
        results = []
        for i, (name, service) in enumerate(zip(base_names[:4], service_types[:4])):
            results.append({
                'name': f'{name} {service}',
                'website': f'https://{name.lower()}{service.lower()}.com',
                'phone': f'(555) {100 + i:03d}-{1000 + i:04d}',
                'address': f'{100 + i * 10} Main St, {geo_location}',
                'rating': round(3.5 + (i * 0.3), 1),
                'review_count': 50 + (i * 25),
                'category': industry or 'General Services',
                'price_level': '$' * (2 + (i % 3)),
                'ranking': i + 1
            })
        
        return results
    
    async def _simulate_social_results(self, platform: str, 
                                     industry: Optional[str]) -> List[Dict[str, Any]]:
        """Simulate social media search results"""
        base_handles = ['proservices', 'expertteam', 'qualitywork', 'localpros']
        
        results = []
        for i, handle in enumerate(base_handles):
            results.append({
                'name': f'{handle.title()} {industry or "Services"}',
                'handle': f'@{handle}{platform[0]}',
                'followers': 1000 + (i * 500),
                'engagement_rate': round(2.5 + (i * 0.5), 1),
                'content_frequency': ['daily', 'weekly', 'bi-weekly', 'monthly'][i],
                'content_themes': ['projects', 'tips', 'testimonials', 'behind-scenes'],
                'last_post_date': f'2024-08-{8 - i:02d}'
            })
        
        return results
    
    def _assess_local_presence_from_search(self, result: Dict[str, Any], geo_location: str) -> Dict[str, Any]:
        """Assess local presence indicators from search results"""
        description = result.get('description', '').lower()
        display_link = result.get('display_link', '').lower()
        
        return {
            'has_geo_in_description': geo_location.lower() in description,
            'has_geo_in_domain': geo_location.lower() in display_link,
            'has_local_keywords': any(keyword in description for keyword in ['local', 'near', 'area', 'serving']),
            'domain_suggests_local': any(indicator in display_link for indicator in [geo_location.lower()[:3], 'local']),
            'description_length': len(result.get('description', '')),
            'appears_commercial': 'business' in description or 'service' in description
        }
    
    def _get_location_coordinates(self, geo_location: str) -> Optional[str]:
        """Convert location name to coordinates for Places API"""
        # Major location coordinates (in production, use Geocoding API)
        location_coords = {
            'US': '39.8283,-98.5795',  # Center of US
            'CA': '56.1304,-106.3468',  # Center of Canada
            'GB': '55.3781,-3.4360',   # Center of UK
            'AU': '-25.2744,133.7751', # Center of Australia
            'DE': '51.1657,10.4515',   # Center of Germany
            'FR': '46.2276,2.2137',    # Center of France
            'ES': '40.4637,-3.7492',   # Center of Spain
            'IT': '41.8719,12.5674',   # Center of Italy
            'JP': '36.2048,138.2529',  # Center of Japan
            'BR': '-14.2350,-51.9253'  # Center of Brazil
        }
        
        return location_coords.get(geo_location)
    
    def _generate_social_search_terms(self, business_url: str, industry: Optional[str]) -> List[str]:
        """Generate search terms for social media discovery"""
        terms = []
        
        if industry:
            terms.extend([
                f"{industry} business",
                f"{industry} services",
                f"{industry} company"
            ])
        
        # Extract domain keywords
        if business_url:
            domain_parts = business_url.replace('https://', '').replace('http://', '').split('.')[0]
            if len(domain_parts) > 3:  # Avoid very short domains
                terms.append(domain_parts)
        
        # Generic business terms
        terms.extend([
            'small business',
            'local business',
            'professional services'
        ])
        
        return terms[:5]  # Limit for API efficiency
    
    def _consolidate_competitors(self, search_competitors: List[Dict], 
                               directory_competitors: List[Dict], 
                               social_competitors: List[Dict]) -> Dict[str, List[Dict]]:
        """Consolidate and categorize competitors from all sources"""
        
        # Combine all competitors
        all_competitors = []
        all_competitors.extend(search_competitors)
        all_competitors.extend(directory_competitors)
        all_competitors.extend(social_competitors)
        
        # Remove duplicates and categorize
        seen_names = set()
        categorized = {
            'direct': [],
            'indirect': [],
            'leaders': [],
            'local': []
        }
        
        for competitor in all_competitors:
            name = competitor.get('name', '').lower()
            if name in seen_names:
                continue
            seen_names.add(name)
            
            # Categorization logic
            if self._is_direct_competitor(competitor):
                categorized['direct'].append(competitor)
            elif self._is_market_leader(competitor):
                categorized['leaders'].append(competitor)
            elif self._is_local_player(competitor):
                categorized['local'].append(competitor)
            else:
                categorized['indirect'].append(competitor)
        
        # Limit each category
        for category in categorized:
            categorized[category] = categorized[category][:8]
        
        return categorized
    
    def _is_direct_competitor(self, competitor: Dict[str, Any]) -> bool:
        """Determine if competitor is a direct competitor"""
        # Check for direct competition indicators
        indicators = [
            competitor.get('discovery_method') == 'search',
            competitor.get('ranking_position', 10) <= 5,
            competitor.get('rating', 0) >= 4.0,
            competitor.get('review_count', 0) >= 50
        ]
        
        return sum(indicators) >= 2
    
    def _is_market_leader(self, competitor: Dict[str, Any]) -> bool:
        """Determine if competitor is a market leader"""
        indicators = [
            competitor.get('followers', 0) >= 5000,
            competitor.get('rating', 0) >= 4.5,
            competitor.get('review_count', 0) >= 200,
            competitor.get('ranking_position', 10) == 1
        ]
        
        return sum(indicators) >= 2
    
    def _is_local_player(self, competitor: Dict[str, Any]) -> bool:
        """Determine if competitor is a local player"""
        local_presence = competitor.get('local_presence', {})
        if isinstance(local_presence, dict):
            local_indicators = sum([
                local_presence.get('has_local_phone', False),
                local_presence.get('has_local_address', False),
                local_presence.get('has_local_reviews', False),
                local_presence.get('geo_targeted_content', False)
            ])
            return local_indicators >= 2
        
        return False