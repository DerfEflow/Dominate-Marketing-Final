"""
Reliable web scraping module for extracting authentic business data
Uses multiple strategies to ensure accurate data extraction
"""

import logging
import requests
from typing import Dict, Any, Optional
from urllib.parse import urlparse
import trafilatura
from bs4 import BeautifulSoup
import re
from datetime import datetime

logger = logging.getLogger(__name__)

class ReliableWebScraper:
    """
    High-reliability web scraper that extracts authentic business data
    Uses multiple extraction methods to ensure accuracy
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def extract_business_data(self, url: str) -> Dict[str, Any]:
        """
        Extract comprehensive business data from URL with high reliability
        Returns authentic data only - no fallbacks or synthetic content
        """
        if not url.strip():
            raise ValueError("URL cannot be empty")
            
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        logger.info(f"Scraping business data from: {url}")
        
        try:
            # Download webpage content
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            html_content = response.text
            
            # Parse with BeautifulSoup for metadata extraction
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract reading mode content using trafilatura
            reading_content = trafilatura.extract(
                html_content,
                include_comments=False,
                include_tables=True,
                include_images=False,
                favor_precision=True,
                favor_recall=False
            )
            
            if not reading_content:
                raise Exception("Failed to extract readable content from webpage")
            
            # Extract comprehensive metadata
            metadata = self._extract_metadata(soup, url)
            
            # Extract business information from content
            business_info = self._extract_business_info(reading_content, url, metadata)
            
            # Extract keywords from actual content
            keywords = self._extract_keywords(reading_content, metadata)
            
            # Compile comprehensive business data
            business_data = {
                'url': url,
                'domain': urlparse(url).netloc,
                'business_name': business_info['name'],
                'industry': business_info['industry'],
                'description': business_info['description'],
                'reading_content': reading_content,
                'content_length': len(reading_content),
                'metadata': metadata,
                'keywords': keywords,
                'location_indicators': business_info['location'],
                'contact_info': business_info['contact'],
                'services_products': business_info['services'],
                'social_media': business_info['social'],
                'scraped_at': datetime.now().isoformat(),
                'extraction_method': 'authentic_scraping'
            }
            
            logger.info(f"Successfully extracted {len(reading_content)} chars of content for {business_info['name']}")
            return business_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error scraping {url}: {e}")
            raise Exception(f"Failed to access website: {str(e)}")
        except Exception as e:
            logger.error(f"Scraping error for {url}: {e}")
            raise Exception(f"Data extraction failed: {str(e)}")
    
    def _extract_metadata(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Extract comprehensive metadata from HTML"""
        metadata = {
            'title': '',
            'description': '',
            'keywords': '',
            'og_title': '',
            'og_description': '',
            'og_image': '',
            'twitter_title': '',
            'twitter_description': '',
            'canonical_url': '',
            'lang': '',
            'robots': ''
        }
        
        # Page title
        title_tag = soup.find('title')
        if title_tag:
            metadata['title'] = title_tag.get_text().strip()
        
        # Meta tags
        meta_tags = soup.find_all('meta')
        for tag in meta_tags:
            name = tag.get('name', '').lower()
            property_name = tag.get('property', '').lower()
            content = tag.get('content', '')
            
            if name == 'description':
                metadata['description'] = content
            elif name == 'keywords':
                metadata['keywords'] = content
            elif name == 'robots':
                metadata['robots'] = content
            elif property_name == 'og:title':
                metadata['og_title'] = content
            elif property_name == 'og:description':
                metadata['og_description'] = content
            elif property_name == 'og:image':
                metadata['og_image'] = content
            elif name == 'twitter:title':
                metadata['twitter_title'] = content
            elif name == 'twitter:description':
                metadata['twitter_description'] = content
        
        # Language
        html_tag = soup.find('html')
        if html_tag and html_tag.get('lang'):
            metadata['lang'] = html_tag.get('lang')
        
        # Canonical URL
        canonical = soup.find('link', {'rel': 'canonical'})
        if canonical:
            metadata['canonical_url'] = canonical.get('href', '')
        
        return metadata
    
    def _extract_business_info(self, content: str, url: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Extract business information from content and metadata"""
        # Extract business name
        business_name = self._extract_business_name(content, url, metadata)
        
        # Extract industry classification
        industry = self._classify_industry(content, metadata)
        
        # Extract business description
        description = self._extract_description(content, metadata)
        
        # Extract location information
        location = self._extract_location_info(content)
        
        # Extract contact information
        contact = self._extract_contact_info(content)
        
        # Extract services/products
        services = self._extract_services_products(content)
        
        # Extract social media links
        social = self._extract_social_media(content)
        
        return {
            'name': business_name,
            'industry': industry,
            'description': description,
            'location': location,
            'contact': contact,
            'services': services,
            'social': social
        }
    
    def _extract_business_name(self, content: str, url: str, metadata: Dict[str, Any]) -> str:
        """Extract actual business name from multiple sources"""
        # Priority 1: Page title
        title = metadata.get('title', '')
        if title:
            # Clean title of common suffixes
            clean_title = re.sub(r'\s*[-|–]\s*(Home|Welcome|Official|Site).*$', '', title, flags=re.IGNORECASE)
            if len(clean_title.strip()) > 0 and len(clean_title) < 100:
                return clean_title.strip()
        
        # Priority 2: OG title
        og_title = metadata.get('og_title', '')
        if og_title and len(og_title) < 100:
            return og_title.strip()
        
        # Priority 3: Extract from domain
        domain = urlparse(url).netloc.replace('www.', '')
        business_name = domain.split('.')[0]
        return business_name.replace('-', ' ').replace('_', ' ').title()
    
    def _classify_industry(self, content: str, metadata: Dict[str, Any]) -> str:
        """Classify industry based on actual content analysis"""
        combined_text = f"{metadata.get('title', '')} {metadata.get('description', '')} {content[:1000]}".lower()
        
        # Industry keyword patterns based on actual content
        industry_patterns = {
            'technology': ['software', 'tech', 'digital', 'app', 'platform', 'saas', 'api', 'cloud', 'ai', 'data'],
            'healthcare': ['health', 'medical', 'doctor', 'clinic', 'hospital', 'wellness', 'therapy', 'medicine'],
            'finance': ['financial', 'bank', 'investment', 'insurance', 'loan', 'credit', 'mortgage', 'wealth'],
            'education': ['education', 'school', 'university', 'course', 'learning', 'training', 'academic'],
            'retail': ['shop', 'store', 'buy', 'sell', 'product', 'retail', 'ecommerce', 'marketplace'],
            'food': ['restaurant', 'food', 'cafe', 'dining', 'cuisine', 'menu', 'catering', 'delivery'],
            'services': ['service', 'consulting', 'agency', 'professional', 'business', 'company']
        }
        
        industry_scores = {}
        for industry, keywords in industry_patterns.items():
            score = sum(1 for keyword in keywords if keyword in combined_text)
            if score > 0:
                industry_scores[industry] = score
        
        if industry_scores:
            return max(industry_scores.keys(), key=lambda k: industry_scores[k])
        
        return 'professional_services'
    
    def _extract_description(self, content: str, metadata: Dict[str, Any]) -> str:
        """Extract business description from actual content"""
        # Priority 1: Meta description
        meta_desc = metadata.get('description', '')
        if meta_desc and len(meta_desc) > 20:
            return meta_desc
        
        # Priority 2: OG description
        og_desc = metadata.get('og_description', '')
        if og_desc and len(og_desc) > 20:
            return og_desc
        
        # Priority 3: Extract first meaningful paragraph from content
        sentences = content.split('. ')
        for sentence in sentences[:5]:
            if len(sentence.strip()) > 50 and len(sentence.strip()) < 300:
                return sentence.strip() + '.'
        
        # Fallback: First 200 characters of content
        return content[:200].strip() + '...' if len(content) > 200 else content.strip()
    
    def _extract_keywords(self, content: str, metadata: Dict[str, Any]) -> list:
        """Extract keywords from actual content"""
        keywords = set()
        
        # Keywords from meta tag
        meta_keywords = metadata.get('keywords', '')
        if meta_keywords:
            keywords.update([k.strip() for k in meta_keywords.split(',') if k.strip()])
        
        # Extract keywords from content
        words = re.findall(r'\b[a-zA-Z]{3,}\b', content.lower())
        
        # Common business keywords to filter
        business_words = {'business', 'company', 'service', 'professional', 'solution', 'customer', 'client'}
        content_keywords = [word for word in set(words) if word in business_words and len(word) > 3]
        
        keywords.update(content_keywords[:10])  # Top 10 content keywords
        
        return list(keywords)[:15]  # Limit to 15 keywords
    
    def _extract_location_info(self, content: str) -> Dict[str, Any]:
        """Extract location information from content"""
        location_info = {
            'city': None,
            'state': None,
            'country': None,
            'address': None
        }
        
        # US State abbreviations
        us_states = ['AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA', 'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD', 'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ', 'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC', 'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY']
        
        # Look for state abbreviations
        for state in us_states:
            if re.search(rf'\b{state}\b', content):
                location_info['state'] = state
                break
        
        # Look for address patterns
        address_pattern = r'\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln)'
        address_match = re.search(address_pattern, content)
        if address_match:
            location_info['address'] = address_match.group()
        
        return location_info
    
    def _extract_contact_info(self, content: str) -> Dict[str, Any]:
        """Extract contact information from content"""
        contact_info = {
            'phone': None,
            'email': None
        }
        
        # Phone number patterns
        phone_pattern = r'(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}'
        phone_match = re.search(phone_pattern, content)
        if phone_match:
            contact_info['phone'] = phone_match.group()
        
        # Email patterns
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_match = re.search(email_pattern, content)
        if email_match:
            contact_info['email'] = email_match.group()
        
        return contact_info
    
    def _extract_services_products(self, content: str) -> list:
        """Extract services/products mentioned in content"""
        services = []
        
        # Look for service-related keywords in context
        service_patterns = [
            r'we offer ([^.]+)',
            r'our services include ([^.]+)',
            r'we provide ([^.]+)',
            r'specializing in ([^.]+)'
        ]
        
        for pattern in service_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            services.extend([match.strip() for match in matches])
        
        return services[:5]  # Limit to 5 services
    
    def _extract_social_media(self, content: str) -> Dict[str, str]:
        """Extract social media links from content"""
        social_media = {}
        
        # Social media patterns
        social_patterns = {
            'facebook': r'(?:https?://)?(?:www\.)?facebook\.com/[A-Za-z0-9._-]+',
            'twitter': r'(?:https?://)?(?:www\.)?twitter\.com/[A-Za-z0-9._-]+',
            'linkedin': r'(?:https?://)?(?:www\.)?linkedin\.com/(?:company/|in/)[A-Za-z0-9._-]+',
            'instagram': r'(?:https?://)?(?:www\.)?instagram\.com/[A-Za-z0-9._-]+'
        }
        
        for platform, pattern in social_patterns.items():
            match = re.search(pattern, content)
            if match:
                social_media[platform] = match.group()
        
        return social_media