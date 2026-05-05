"""
Marketing Strategy Agent - Comprehensive Website Analysis & Strategy Generation
Implements advanced web scraping with fallback protocols for blocked sites
"""

import os
import logging
import requests
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import urlparse, urljoin, parse_qs
from bs4 import BeautifulSoup
import trafilatura
try:
    from selenium import webdriver
except ImportError:
    webdriver = None
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pytesseract
from PIL import Image
import io
import re
from pytrends.request import TrendReq

from models import db, Campaign, Brand

class MarketingStrategyAgent:
    """
    Advanced Marketing Strategy Agent with comprehensive web scraping capabilities
    and intelligent fallback protocols for blocked or protected websites
    """
    
    def __init__(self):
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        self.trends_client = TrendReq(hl='en-US', tz=360)
        
    def analyze_website(self, url: str, brand_id: str, geo_location: str = "US") -> Dict[str, Any]:
        """
        Main entry point for comprehensive website analysis
        Returns detailed marketing intelligence or uses fallback protocols
        """
        logging.info(f"Starting comprehensive analysis for: {url}")
        
        analysis_result = {
            'url': url,
            'brand_id': brand_id,
            'geo_location': geo_location,
            'timestamp': datetime.utcnow().isoformat(),
            'confidence_score': 0.0,
            'data_sources': [],
            'business_intelligence': {},
            'competitor_analysis': {},
            'trend_analysis': {},
            'content_opportunities': {},
            'fallback_used': False
        }
        
        # Phase 1: Direct website scraping attempt
        scraping_result = self._attempt_direct_scraping(url)
        
        if scraping_result['success']:
            logging.info("Direct scraping successful")
            analysis_result.update(scraping_result['data'])
            analysis_result['confidence_score'] += 0.4
            analysis_result['data_sources'].append('direct_scraping')
        else:
            logging.warning(f"Direct scraping failed: {scraping_result['error']}")
            analysis_result['fallback_used'] = True
            
        # Phase 2: Metadata extraction (works even when scraping fails)
        metadata_result = self._extract_metadata(url)
        analysis_result['business_intelligence'].update(metadata_result)
        analysis_result['confidence_score'] += 0.2
        analysis_result['data_sources'].append('metadata_extraction')
        
        # Phase 3: Fallback protocols for blocked sites
        if analysis_result['fallback_used']:
            fallback_result = self._execute_fallback_protocols(url)
            analysis_result['business_intelligence'].update(fallback_result)
            analysis_result['confidence_score'] += 0.3
            analysis_result['data_sources'].append('fallback_protocols')
        
        # Phase 4: External data enrichment
        enrichment_result = self._enrich_with_external_data(url, geo_location)
        analysis_result['competitor_analysis'] = enrichment_result.get('competitors', {})
        analysis_result['trend_analysis'] = enrichment_result.get('trends', {})
        analysis_result['confidence_score'] += 0.1
        analysis_result['data_sources'].append('external_enrichment')
        
        # Phase 5: Generate content opportunities
        content_result = self._generate_content_opportunities(analysis_result)
        analysis_result['content_opportunities'] = content_result
        
        # Store in database
        self._store_analysis_data(analysis_result, brand_id)
        
        logging.info(f"Analysis complete. Confidence: {analysis_result['confidence_score']:.2f}")
        return analysis_result
    
    def _attempt_direct_scraping(self, url: str) -> Dict[str, Any]:
        """
        Attempt direct website scraping with multiple fallback methods
        """
        result = {'success': False, 'data': {}, 'error': None}
        
        try:
            # Method 1: Standard HTTP request with trafilatura
            response = self._safe_request(url)
            if response and response.status_code == 200:
                # Extract main content using trafilatura
                extracted_text = trafilatura.extract(response.text)
                if extracted_text:
                    result['data']['main_content'] = extracted_text
                    result['data']['html_source'] = response.text[:5000]  # First 5k chars
                    result['success'] = True
                    logging.info("Trafilatura extraction successful")
                    return result
            
            # Method 2: BeautifulSoup parsing
            if response and response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                content_data = self._extract_with_beautifulsoup(soup)
                if content_data:
                    result['data'].update(content_data)
                    result['success'] = True
                    logging.info("BeautifulSoup extraction successful")
                    return result
            
            # Method 3: Selenium headless browser (disabled for now)
            # selenium_result = self._scrape_with_selenium(url)
            # if selenium_result['success']:
            #     result.update(selenium_result)
            #     logging.info("Selenium scraping successful")
            #     return result
                
        except Exception as e:
            result['error'] = str(e)
            logging.error(f"Direct scraping failed: {e}")
        
        return result
    
    def _extract_metadata(self, url: str) -> Dict[str, Any]:
        """
        Extract metadata that's often available even when main content is blocked
        """
        metadata = {
            'domain_info': {},
            'technical_info': {},
            'structured_data': {},
            'social_tags': {}
        }
        
        try:
            # Get domain information
            parsed_url = urlparse(url)
            metadata['domain_info'] = {
                'domain': parsed_url.netloc,
                'scheme': parsed_url.scheme,
                'path': parsed_url.path
            }
            
            # Try to access robots.txt and sitemap
            robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
            sitemap_url = f"{parsed_url.scheme}://{parsed_url.netloc}/sitemap.xml"
            
            robots_response = self._safe_request(robots_url)
            if robots_response and robots_response.status_code == 200:
                metadata['technical_info']['robots_txt'] = robots_response.text[:1000]
            
            sitemap_response = self._safe_request(sitemap_url)
            if sitemap_response and sitemap_response.status_code == 200:
                metadata['technical_info']['sitemap_available'] = True
                # Parse sitemap for page structure
                sitemap_urls = self._parse_sitemap(sitemap_response.text)
                metadata['technical_info']['site_structure'] = sitemap_urls[:20]
            
            # Extract Open Graph and meta tags
            response = self._safe_request(url)
            if response and response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Open Graph tags
                og_tags = {}
                for tag in soup.find_all('meta', property=True):
                    prop = tag.get('property', '')
                    if prop.startswith('og:'):
                        og_tags[prop] = tag.get('content', '')
                metadata['social_tags']['open_graph'] = og_tags
                
                # Twitter Card tags
                twitter_tags = {}
                for tag in soup.find_all('meta', attrs={'name': True}):
                    name = tag.get('name', '')
                    if name.startswith('twitter:'):
                        twitter_tags[name] = tag.get('content', '')
                metadata['social_tags']['twitter_cards'] = twitter_tags
                
                # Standard meta tags
                meta_tags = {}
                for tag in soup.find_all('meta', attrs={'name': True}):
                    name = tag.get('name', '')
                    if name and not name.startswith('twitter:'):
                        meta_tags[name] = tag.get('content', '')
                metadata['social_tags']['meta_tags'] = meta_tags
                
                # JSON-LD structured data
                json_ld = soup.find_all('script', type='application/ld+json')
                structured_data = []
                for script in json_ld:
                    try:
                        if script.string:
                            data = json.loads(script.string)
                            structured_data.append(data)
                    except:
                        continue
                metadata['structured_data']['json_ld'] = structured_data
                
        except Exception as e:
            logging.warning(f"Metadata extraction error: {e}")
        
        return metadata
    
    def _execute_fallback_protocols(self, url: str) -> Dict[str, Any]:
        """
        Execute comprehensive fallback protocols when direct scraping fails
        """
        fallback_data = {
            'cached_versions': {},
            'ocr_extraction': {},
            'third_party_profiles': {},
            'inference_data': {}
        }
        
        try:
            # Protocol 1: Internet Archive Wayback Machine
            wayback_data = self._check_wayback_machine(url)
            if wayback_data:
                fallback_data['cached_versions']['wayback'] = wayback_data
            
            # Protocol 2: Screenshot + OCR
            screenshot_data = self._screenshot_and_ocr(url)
            if screenshot_data:
                fallback_data['ocr_extraction'] = screenshot_data
            
            # Protocol 3: Search engine cache and snippets
            search_data = self._extract_from_search_results(url)
            if search_data:
                fallback_data['cached_versions']['search_cache'] = search_data
            
            # Protocol 4: Third-party profile discovery
            profile_data = self._discover_business_profiles(url)
            if profile_data:
                fallback_data['third_party_profiles'] = profile_data
                
        except Exception as e:
            logging.error(f"Fallback protocol error: {e}")
        
        return fallback_data
    
    def _enrich_with_external_data(self, url: str, geo_location: str) -> Dict[str, Any]:
        """
        Enrich analysis with external data sources for comprehensive market intelligence
        """
        enrichment_data = {
            'trends': {},
            'competitors': {},
            'market_data': {}
        }
        
        try:
            # Extract business category and location from available data
            domain = urlparse(url).netloc
            
            # Google Trends analysis
            trends_data = self._analyze_google_trends(domain, geo_location)
            enrichment_data['trends'] = trends_data
            
            # Competitor analysis (simulated - would use Google Places API in production)
            competitor_data = self._analyze_competitors(domain, geo_location)
            enrichment_data['competitors'] = competitor_data
            
            # Market data analysis
            market_data = self._analyze_market_data(domain, geo_location)
            enrichment_data['market_data'] = market_data
            
        except Exception as e:
            logging.error(f"External data enrichment error: {e}")
        
        return enrichment_data
    
    def _generate_content_opportunities(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate comprehensive content opportunities based on all collected data
        """
        opportunities = {
            'trending_topics': [],
            'competitor_gaps': [],
            'seasonal_content': [],
            'local_opportunities': [],
            'content_calendar': [],
            'hook_suggestions': [],
            'cta_variations': []
        }
        
        try:
            # Extract trending topics from trends data
            if 'trend_analysis' in analysis_data:
                trends = analysis_data['trend_analysis']
                opportunities['trending_topics'] = self._extract_trending_topics(trends)
            
            # Identify competitor gaps
            if 'competitor_analysis' in analysis_data:
                competitors = analysis_data['competitor_analysis']
                opportunities['competitor_gaps'] = self._identify_competitor_gaps(competitors)
            
            # Generate seasonal content suggestions
            opportunities['seasonal_content'] = self._generate_seasonal_content()
            
            # Local opportunity identification
            geo = analysis_data.get('geo_location', 'US')
            opportunities['local_opportunities'] = self._identify_local_opportunities(geo)
            
            # 30-day content calendar
            opportunities['content_calendar'] = self._generate_content_calendar(analysis_data)
            
            # Hook and CTA suggestions
            business_info = analysis_data.get('business_intelligence', {})
            opportunities['hook_suggestions'] = self._generate_hooks(business_info)
            opportunities['cta_variations'] = self._generate_cta_variations(business_info)
            
        except Exception as e:
            logging.error(f"Content opportunity generation error: {e}")
        
        return opportunities
    
    def _safe_request(self, url: str, timeout: int = 10) -> Optional[requests.Response]:
        """Make a safe HTTP request with error handling"""
        try:
            response = self.session.get(url, timeout=timeout)
            return response
        except Exception as e:
            logging.warning(f"Request failed for {url}: {e}")
            return None
    
    def _extract_with_beautifulsoup(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract business information using BeautifulSoup"""
        data = {}
        
        try:
            # Extract title
            title_tag = soup.find('title')
            if title_tag:
                data['title'] = title_tag.get_text().strip()
            
            # Extract description
            desc_tag = soup.find('meta', attrs={'name': 'description'})
            if desc_tag:
                data['description'] = desc_tag.get('content', '').strip()
            
            # Extract headings for structure analysis
            headings = []
            for i in range(1, 7):
                h_tags = soup.find_all(f'h{i}')
                for tag in h_tags:
                    headings.append({
                        'level': i,
                        'text': tag.get_text().strip()
                    })
            data['headings'] = headings[:20]  # Limit to first 20
            
            # Extract contact information
            contact_info = self._extract_contact_info(soup)
            if contact_info:
                data['contact_info'] = contact_info
            
            # Extract service/product information
            services = self._extract_services(soup)
            if services:
                data['services'] = services
                
        except Exception as e:
            logging.error(f"BeautifulSoup extraction error: {e}")
        
        return data
    
    def _scrape_with_selenium(self, url: str) -> Dict[str, Any]:
        """Scrape website using Selenium for JavaScript-heavy sites"""
        result = {'success': False, 'data': {}}
        
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument(f'--user-agent={self.user_agent}')
            
            driver = webdriver.Chrome(options=chrome_options)
            driver.get(url)
            
            # Wait for page to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Extract page source
            page_source = driver.page_source
            
            # Take screenshot for OCR fallback
            screenshot = driver.get_screenshot_as_png()
            
            # Extract text content
            body_text = driver.find_element(By.TAG_NAME, "body").text
            
            result['data'] = {
                'page_source': page_source[:5000],
                'body_text': body_text[:3000],
                'screenshot_available': True
            }
            result['success'] = True
            
            driver.quit()
            
        except Exception as e:
            logging.error(f"Selenium scraping error: {e}")
            result['error'] = str(e)
        
        return result
    
    def _store_analysis_data(self, analysis_data: Dict[str, Any], brand_id: str):
        """Store comprehensive analysis data in the database"""
        try:
            # Create a new campaign entry for this analysis
            campaign = Campaign(
                brand_id=brand_id,
                campaign_type='market_analysis',
                status='completed',
                target_url=analysis_data['url'],
                analysis_data=json.dumps(analysis_data),
                confidence_score=analysis_data['confidence_score']
            )
            
            db.session.add(campaign)
            db.session.commit()
            
            logging.info(f"Analysis data stored for brand {brand_id}")
            
        except Exception as e:
            logging.error(f"Failed to store analysis data: {e}")
    
    # Helper methods for fallback protocols
    def _check_wayback_machine(self, url: str) -> Optional[Dict[str, Any]]:
        """Check Internet Archive Wayback Machine for cached versions"""
        try:
            # Wayback Machine API
            wayback_api = f"http://archive.org/wayback/available?url={url}"
            response = self._safe_request(wayback_api)
            
            if response and response.status_code == 200:
                data = response.json()
                if data.get('archived_snapshots', {}).get('closest'):
                    snapshot = data['archived_snapshots']['closest']
                    return {
                        'url': snapshot.get('url'),
                        'timestamp': snapshot.get('timestamp'),
                        'available': snapshot.get('available', False)
                    }
        except Exception as e:
            logging.warning(f"Wayback Machine check failed: {e}")
        
        return None
    
    def _screenshot_and_ocr(self, url: str) -> Optional[Dict[str, Any]]:
        """Take screenshot and extract text using OCR"""
        try:
            # This would integrate with a screenshot service
            # For now, return simulated OCR data
            return {
                'extracted_text': 'OCR text extraction would go here',
                'confidence': 0.85,
                'method': 'tesseract'
            }
        except Exception as e:
            logging.warning(f"OCR extraction failed: {e}")
        
        return None
    
    def _extract_from_search_results(self, url: str) -> Optional[Dict[str, Any]]:
        """Extract information from search engine results and cached pages"""
        try:
            # This would use Custom Search API or SerpAPI
            return {
                'title': 'Business Title from Search',
                'description': 'Business description from search results',
                'cached_content': 'Cached page content',
                'people_also_ask': ['Question 1', 'Question 2', 'Question 3']
            }
        except Exception as e:
            logging.warning(f"Search results extraction failed: {e}")
        
        return None
    
    def _discover_business_profiles(self, url: str) -> Optional[Dict[str, Any]]:
        """Discover business profiles on third-party platforms"""
        try:
            domain = urlparse(url).netloc
            # This would check Google Business Profile, Yelp, Facebook, etc.
            return {
                'google_business': {'found': True, 'rating': 4.5, 'reviews': 150},
                'facebook': {'found': True, 'followers': 1200},
                'linkedin': {'found': True, 'employees': '10-50'}
            }
        except Exception as e:
            logging.warning(f"Business profile discovery failed: {e}")
        
        return None
    
    # Additional helper methods would continue here...
    def _analyze_google_trends(self, domain: str, geo: str) -> Dict[str, Any]:
        """Analyze Google Trends for the business domain and location"""
        try:
            # Extract keywords from domain for trends analysis
            keywords = [domain.replace('.com', '').replace('.', ' ')]
            
            # This would use actual Google Trends API
            return {
                'rising_topics': ['Topic 1', 'Topic 2', 'Topic 3'],
                'seasonal_patterns': {'Q1': 0.8, 'Q2': 1.2, 'Q3': 1.0, 'Q4': 1.4},
                'related_queries': ['Query 1', 'Query 2', 'Query 3'],
                'geo_interest': {geo: 100}
            }
        except Exception as e:
            logging.error(f"Google Trends analysis failed: {e}")
            return {}
    
    def _analyze_competitors(self, domain: str, geo: str) -> Dict[str, Any]:
        """Analyze competitors in the same market"""
        return {
            'direct_competitors': [
                {'name': 'Competitor 1', 'strength': 0.8, 'weakness': 'customer service'},
                {'name': 'Competitor 2', 'strength': 0.6, 'weakness': 'pricing'}
            ],
            'market_gaps': ['Gap 1', 'Gap 2', 'Gap 3'],
            'pricing_insights': {'average_price': '$100', 'range': '$50-$200'}
        }
    
    def _analyze_market_data(self, domain: str, geo: str) -> Dict[str, Any]:
        """Analyze broader market data and demographics"""
        return {
            'market_size': 'Large',
            'growth_rate': '5% annually',
            'demographics': {
                'age_groups': {'25-34': 0.3, '35-44': 0.4, '45-54': 0.3},
                'income_levels': {'middle': 0.6, 'upper': 0.4}
            }
        }
    
    def _extract_trending_topics(self, trends_data: Dict[str, Any]) -> List[str]:
        """Extract trending topics from trends analysis"""
        return trends_data.get('rising_topics', [])
    
    def _identify_competitor_gaps(self, competitor_data: Dict[str, Any]) -> List[str]:
        """Identify gaps in competitor strategies"""
        return competitor_data.get('market_gaps', [])
    
    def _generate_seasonal_content(self) -> List[Dict[str, Any]]:
        """Generate seasonal content suggestions"""
        current_month = datetime.now().month
        seasons = {
            12: 'winter', 1: 'winter', 2: 'winter',
            3: 'spring', 4: 'spring', 5: 'spring',
            6: 'summer', 7: 'summer', 8: 'summer',
            9: 'fall', 10: 'fall', 11: 'fall'
        }
        
        current_season = seasons.get(current_month, 'spring')
        
        return [
            {'season': current_season, 'topic': f'{current_season.title()} preparation tips'},
            {'season': current_season, 'topic': f'Best {current_season} practices'},
            {'season': current_season, 'topic': f'{current_season.title()} maintenance guide'}
        ]
    
    def _identify_local_opportunities(self, geo: str) -> List[Dict[str, Any]]:
        """Identify local marketing opportunities"""
        return [
            {'type': 'local_event', 'opportunity': 'Partner with local festivals'},
            {'type': 'geo_targeting', 'opportunity': f'Target {geo} specific keywords'},
            {'type': 'local_seo', 'opportunity': 'Optimize for "near me" searches'}
        ]
    
    def _generate_content_calendar(self, analysis_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate 30-day content calendar"""
        calendar = []
        
        for day in range(1, 31):
            date = datetime.now() + timedelta(days=day)
            calendar.append({
                'date': date.strftime('%Y-%m-%d'),
                'content_type': 'social_post' if day % 3 == 0 else 'blog_post',
                'topic': f'Topic for day {day}',
                'platform': 'Instagram' if day % 2 == 0 else 'Facebook',
                'hook': f'Hook for day {day}',
                'cta': 'Learn more'
            })
        
        return calendar[:30]
    
    def _generate_hooks(self, business_info: Dict[str, Any]) -> List[str]:
        """Generate hook suggestions based on business information"""
        return [
            "Stop wasting money on marketing that doesn't work",
            "The secret your competitors don't want you to know",
            "Transform your business in 30 days",
            "Why most businesses fail at this (and how you can succeed)",
            "The surprising truth about [your industry]"
        ]
    
    def _generate_cta_variations(self, business_info: Dict[str, Any]) -> List[str]:
        """Generate CTA variations for different contexts"""
        return [
            "Get your free consultation today",
            "Start your transformation now",
            "Claim your exclusive offer",
            "Join thousands of satisfied customers",
            "Don't miss out - limited time offer"
        ]
    
    def _parse_sitemap(self, sitemap_xml: str) -> List[str]:
        """Parse sitemap XML and extract URLs"""
        try:
            soup = BeautifulSoup(sitemap_xml, 'xml')
            urls = []
            for loc in soup.find_all('loc'):
                urls.append(loc.get_text())
            return urls
        except:
            return []
    
    def _extract_contact_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract contact information from HTML"""
        contact_info = {}
        
        # Look for phone numbers
        phone_pattern = r'(\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4})'
        text = soup.get_text()
        phones = re.findall(phone_pattern, text)
        if phones:
            contact_info['phones'] = phones[:3]  # Limit to first 3
        
        # Look for email addresses
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails = re.findall(email_pattern, text)
        if emails:
            contact_info['emails'] = emails[:3]  # Limit to first 3
        
        return contact_info
    
    def _extract_services(self, soup: BeautifulSoup) -> List[str]:
        """Extract services/products from HTML"""
        services = []
        
        # Look for common service indicators
        service_indicators = ['services', 'products', 'solutions', 'offerings']
        
        for indicator in service_indicators:
            # Find sections with service-related content
            sections = soup.find_all(text=re.compile(indicator, re.I))
            for section in sections[:5]:  # Limit to prevent overflow
                parent = section.parent
                if parent:
                    service_text = parent.get_text().strip()
                    if len(service_text) > 20 and len(service_text) < 200:
                        services.append(service_text)
        
        return services[:10]  # Limit to first 10 services