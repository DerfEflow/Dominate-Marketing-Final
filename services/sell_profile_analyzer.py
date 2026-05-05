"""
Sell Profile Analyzer - Extracts comprehensive business intelligence
Creates detailed business profiles from websites and social media data
"""

import logging
import requests
import trafilatura
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Any
import re
import json
import base64
import os
import tempfile
from dataclasses import dataclass, asdict
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class SellProfile:
    """Complete business profile extracted from website and social media"""
    url: str
    business_name: str
    industry: str
    geography: Dict[str, Any]
    metadata: Dict[str, Any]
    keywords: List[str]
    about_section: str
    distinctives: List[str]
    social_media: Dict[str, Any]
    extracted_at: str
    confidence_score: float

class SellProfileAnalyzer:
    """Extracts comprehensive business intelligence to create Sell Profiles"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Industry classification patterns
        self.industry_patterns = {
            'construction': ['roofing', 'construction', 'contractor', 'building', 'renovation', 'remodeling', 'home improvement'],
            'healthcare': ['dental', 'medical', 'health', 'clinic', 'doctor', 'physician', 'therapy', 'wellness'],
            'legal': ['law', 'attorney', 'lawyer', 'legal', 'firm', 'counsel', 'litigation'],
            'automotive': ['auto', 'car', 'automotive', 'vehicle', 'repair', 'garage', 'mechanic'],
            'restaurant': ['restaurant', 'food', 'dining', 'cafe', 'catering', 'culinary', 'kitchen'],
            'retail': ['store', 'shop', 'retail', 'boutique', 'market', 'sales'],
            'technology': ['tech', 'software', 'digital', 'it', 'computer', 'web', 'app'],
            'real_estate': ['real estate', 'realtor', 'property', 'homes', 'realty'],
            'finance': ['financial', 'insurance', 'banking', 'investment', 'accounting'],
            'beauty': ['salon', 'spa', 'beauty', 'hair', 'cosmetic', 'skincare'],
            'fitness': ['gym', 'fitness', 'training', 'yoga', 'exercise', 'sport'],
            'education': ['school', 'education', 'learning', 'academy', 'tutor']
        }
        
        # Geographic indicators
        self.geo_patterns = {
            'city_indicators': ['downtown', 'metro', 'city', 'area', 'local', 'neighborhood'],
            'state_abbreviations': ['AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA', 'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD', 'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ', 'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC', 'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY'],
            'region_keywords': ['north', 'south', 'east', 'west', 'central', 'greater', 'county']
        }
    
    def analyze_website(self, url: str) -> SellProfile:
        """Extract complete Sell Profile from website"""
        logger.info(f"Starting Sell Profile analysis for {url}")
        
        try:
            # Extract website content with fallbacks
            content = self._extract_website_content(url)
            
            # Extract business intelligence components
            business_name = self._extract_business_name(url, content)
            industry = self._classify_industry(url, content)
            geography = self._extract_geography(url, content)
            metadata = self._extract_metadata(url, content)
            keywords = self._extract_keywords(content)
            about_section = self._extract_about_section(content)
            distinctives = self._extract_distinctives(content)
            social_media = self._find_social_media_links(url, content)
            
            # Calculate confidence score
            confidence = self._calculate_confidence_score(
                business_name, industry, geography, keywords, about_section
            )
            
            profile = SellProfile(
                url=url,
                business_name=business_name,
                industry=industry,
                geography=geography,
                metadata=metadata,
                keywords=keywords,
                about_section=about_section,
                distinctives=distinctives,
                social_media=social_media,
                extracted_at=datetime.now().isoformat(),
                confidence_score=confidence
            )
            
            logger.info(f"Sell Profile created with {confidence:.2f} confidence")
            return profile
            
        except Exception as e:
            logger.error(f"Error creating Sell Profile for {url}: {e}")
            # Return fallback profile based on URL analysis
            return self._create_fallback_profile(url)
    
    def _extract_website_content(self, url: str) -> str:
        """
        Extract website content using a 4-tier fallback strategy:
          Tier 1: trafilatura  (fast, handles most static sites)
          Tier 2: BeautifulSoup (fallback for trafilatura failures)
          Tier 3: Playwright headless browser (JS-rendered / SPA sites)
          Tier 4: Claude Vision on screenshot (last resort for heavily restricted sites)
        """
        # --- Tier 1: trafilatura ---
        try:
            downloaded = trafilatura.fetch_url(url)
            if downloaded:
                extracted = trafilatura.extract(downloaded)
                if extracted and len(extracted) > 150:
                    logger.info(f"[Scraper Tier 1] trafilatura succeeded for {url}")
                    return extracted
        except Exception as e:
            logger.warning(f"[Scraper Tier 1] trafilatura failed: {e}")

        # --- Tier 2: BeautifulSoup ---
        try:
            response = self.session.get(url, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                for element in soup(['script', 'style', 'nav', 'footer', 'aside']):
                    element.decompose()
                main_content = ""
                for selector in ['main', 'article', '.content', '#content', '.main', 'body']:
                    element = soup.select_one(selector)
                    if element:
                        main_content = element.get_text(strip=True, separator=' ')
                        if len(main_content) > 150:
                            break
                if main_content:
                    logger.info(f"[Scraper Tier 2] BeautifulSoup succeeded for {url}")
                    return main_content[:10000]
        except Exception as e:
            logger.warning(f"[Scraper Tier 2] BeautifulSoup failed: {e}")

        # --- Tier 3: Playwright headless browser ---
        playwright_content = self._extract_with_playwright(url)
        if playwright_content and len(playwright_content) > 150:
            logger.info(f"[Scraper Tier 3] Playwright succeeded for {url}")
            return playwright_content

        # --- Tier 4: Claude Vision screenshot ---
        vision_content = self._extract_with_claude_vision(url)
        if vision_content and len(vision_content) > 50:
            logger.info(f"[Scraper Tier 4] Claude Vision succeeded for {url}")
            return vision_content

        # --- Final fallback: URL-based intelligence ---
        logger.warning(f"[Scraper] All tiers failed for {url}, using URL analysis")
        return self._generate_url_based_content(url)

    def _extract_with_playwright(self, url: str) -> str:
        """
        Tier 3: Use Playwright headless Chromium to render JS-heavy sites
        and extract full page text after JavaScript execution.
        """
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            logger.info("[Scraper Tier 3] Playwright not installed, skipping")
            return ""

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
                page = browser.new_page()
                page.set_extra_http_headers({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
                page.goto(url, wait_until="networkidle", timeout=20000)
                # Wait a moment for any lazy-loaded content
                page.wait_for_timeout(2000)
                # Extract visible text, stripping script/style
                text = page.evaluate("""() => {
                    const unwanted = document.querySelectorAll('script, style, nav, footer, aside, .cookie-banner, #cookie');
                    unwanted.forEach(el => el.remove());
                    return document.body ? document.body.innerText : '';
                }""")
                browser.close()
                return (text or "")[:10000]
        except Exception as e:
            logger.warning(f"[Scraper Tier 3] Playwright extraction failed: {e}")
            return ""

    def _extract_with_claude_vision(self, url: str) -> str:
        """
        Tier 4: Take a screenshot of the page with Playwright and send it
        to Claude Vision for structured business intelligence extraction.
        Falls back gracefully if Playwright or Anthropic SDK are unavailable.
        """
        screenshot_bytes = self._take_screenshot(url)
        if not screenshot_bytes:
            return ""

        anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not anthropic_key:
            logger.warning("[Scraper Tier 4] No ANTHROPIC_API_KEY configured, skipping Vision")
            return ""

        try:
            import anthropic
            client = anthropic.Anthropic(api_key=anthropic_key)
            image_b64 = base64.standard_b64encode(screenshot_bytes).decode("utf-8")

            response = client.messages.create(
                model="claude-opus-4-5",
                max_tokens=1500,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": image_b64,
                            },
                        },
                        {
                            "type": "text",
                            "text": (
                                "You are analyzing a business website screenshot for marketing intelligence. "
                                "Extract and return as plain text:\n"
                                "1. Business name\n"
                                "2. What they sell or offer (products/services)\n"
                                "3. Their apparent target audience\n"
                                "4. Any unique selling points or differentiators\n"
                                "5. Industry or business category\n"
                                "6. Location or geographic focus if visible\n"
                                "7. Any taglines, slogans, or key marketing messages\n"
                                "8. Contact info if visible (phone, email, address)\n\n"
                                "Be specific and detailed. This will be used to generate marketing content."
                            ),
                        },
                    ],
                }],
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"[Scraper Tier 4] Claude Vision analysis failed: {e}")
            return ""

    def _take_screenshot(self, url: str) -> bytes:
        """Take a full-page screenshot using Playwright. Returns PNG bytes or empty bytes."""
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            return b""

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
                page = browser.new_page(viewport={"width": 1280, "height": 900})
                page.set_extra_http_headers({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
                page.goto(url, wait_until="networkidle", timeout=20000)
                page.wait_for_timeout(2000)
                screenshot = page.screenshot(full_page=False)  # viewport shot is enough for Vision
                browser.close()
                return screenshot
        except Exception as e:
            logger.warning(f"[Scraper] Screenshot failed for {url}: {e}")
            return b""
    
    def _generate_url_based_content(self, url: str) -> str:
        """Generate intelligent content from URL structure when scraping fails"""
        parsed = urlparse(url.lower())
        domain = parsed.netloc.replace('www.', '')
        path = parsed.path
        
        # Extract business name
        business_name = domain.split('.')[0].replace('-', ' ').replace('_', ' ').title()
        
        # Detect industry from URL
        full_url_text = f"{domain} {path}".lower()
        detected_industry = None
        
        for industry, keywords in self.industry_patterns.items():
            if any(keyword in full_url_text for keyword in keywords):
                detected_industry = industry
                break
        
        # Generate contextual content
        content_parts = [f"{business_name} professional services"]
        
        if detected_industry:
            content_parts.extend([
                f"{detected_industry} industry specialist",
                f"professional {detected_industry} services",
                f"experienced {detected_industry} provider"
            ])
        
        # Add path-based context
        if 'about' in path:
            content_parts.append("company information and background")
        if 'services' in path:
            content_parts.append("comprehensive service offerings")
        if 'contact' in path:
            content_parts.append("customer contact and location information")
        
        return ". ".join(content_parts) + "."
    
    def _extract_business_name(self, url: str, content: str) -> str:
        """Extract business name from URL and content"""
        # Try to find business name in content first
        lines = content.split('\n')[:20]  # Check first 20 lines
        for line in lines:
            line = line.strip()
            if len(line) > 3 and len(line) < 50 and not line.startswith(('http', 'www')):
                # Check if it looks like a business name
                if any(word in line.lower() for word in ['llc', 'inc', 'corp', 'company', 'group']):
                    return line
        
        # Fallback to domain-based extraction
        domain = urlparse(url).netloc.replace('www.', '')
        business_name = domain.split('.')[0]
        return re.sub(r'[^a-zA-Z\s]', ' ', business_name).title().strip()
    
    def _classify_industry(self, url: str, content: str) -> str:
        """Classify business industry from URL and content"""
        full_text = f"{url} {content}".lower()
        
        # Score each industry based on keyword matches
        industry_scores = {}
        for industry, keywords in self.industry_patterns.items():
            score = sum(1 for keyword in keywords if keyword in full_text)
            if score > 0:
                industry_scores[industry] = score
        
        if industry_scores:
            return max(industry_scores.keys(), key=lambda k: industry_scores[k])
        
        return "professional_services"  # Default fallback
    
    def _extract_geography(self, url: str, content: str) -> Dict[str, Any]:
        """Extract geographic information"""
        geography = {
            'city': None,
            'state': None,
            'region': None,
            'country': 'US',  # Default assumption
            'indicators': []
        }
        
        full_text = f"{url} {content}".lower()
        
        # Look for state abbreviations and full state names
        for state in self.geo_patterns['state_abbreviations']:
            if f" {state.lower()} " in f" {full_text} " or f"/{state.lower()}/" in full_text:
                geography['state'] = state
                break
        
        # Also check for full state names
        state_names = {
            'alabama': 'AL', 'alaska': 'AK', 'arizona': 'AZ', 'arkansas': 'AR', 'california': 'CA',
            'colorado': 'CO', 'connecticut': 'CT', 'delaware': 'DE', 'florida': 'FL', 'georgia': 'GA',
            'hawaii': 'HI', 'idaho': 'ID', 'illinois': 'IL', 'indiana': 'IN', 'iowa': 'IA',
            'kansas': 'KS', 'kentucky': 'KY', 'louisiana': 'LA', 'maine': 'ME', 'maryland': 'MD',
            'massachusetts': 'MA', 'michigan': 'MI', 'minnesota': 'MN', 'mississippi': 'MS', 'missouri': 'MO',
            'montana': 'MT', 'nebraska': 'NE', 'nevada': 'NV', 'new hampshire': 'NH', 'new jersey': 'NJ',
            'new mexico': 'NM', 'new york': 'NY', 'north carolina': 'NC', 'north dakota': 'ND', 'ohio': 'OH',
            'oklahoma': 'OK', 'oregon': 'OR', 'pennsylvania': 'PA', 'rhode island': 'RI', 'south carolina': 'SC',
            'south dakota': 'SD', 'tennessee': 'TN', 'texas': 'TX', 'utah': 'UT', 'vermont': 'VT',
            'virginia': 'VA', 'washington': 'WA', 'west virginia': 'WV', 'wisconsin': 'WI', 'wyoming': 'WY'
        }
        
        if not geography['state']:
            for state_name, abbr in state_names.items():
                if state_name in full_text:
                    geography['state'] = abbr
                    break
        
        # Look for geographic indicators
        for indicator in self.geo_patterns['city_indicators']:
            if indicator in full_text:
                geography['indicators'].append(indicator)
        
        # Look for region keywords
        for region in self.geo_patterns['region_keywords']:
            if region in full_text:
                geography['region'] = region
                break
        
        return geography
    
    def _extract_metadata(self, url: str, content: str) -> Dict[str, Any]:
        """Extract metadata and technical information"""
        return {
            'domain': urlparse(url).netloc,
            'content_length': len(content),
            'has_contact_info': any(word in content.lower() for word in ['phone', 'email', 'contact']),
            'has_services_page': '/services' in url.lower() or 'services' in content.lower(),
            'has_about_page': '/about' in url.lower() or 'about' in content.lower(),
            'extracted_method': 'direct_scraping' if len(content) > 500 else 'url_analysis'
        }
    
    def _extract_keywords(self, content: str) -> List[str]:
        """Extract relevant business keywords from content"""
        # Extract words from content
        words = re.findall(r'\b[a-zA-Z]{3,}\b', content.lower())
        
        # Comprehensive stop words list
        stopwords = {
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her', 'was', 'one', 'our', 'out', 
            'day', 'get', 'has', 'him', 'his', 'how', 'man', 'new', 'now', 'old', 'see', 'two', 'way', 'who', 'boy', 
            'did', 'its', 'let', 'put', 'say', 'she', 'too', 'use', 'your', 'this', 'that', 'they', 'them', 'than',
            'will', 'with', 'have', 'from', 'they', 'know', 'want', 'been', 'good', 'much', 'some', 'time', 'very',
            'when', 'come', 'here', 'just', 'like', 'long', 'make', 'many', 'over', 'such', 'take', 'than', 'them',
            'well', 'were', 'what', 'call', 'each', 'which', 'their', 'said', 'there', 'after', 'back', 'other',
            'first', 'work', 'life', 'only', 'right', 'think', 'little', 'down', 'before', 'also', 'around',
            'contact', 'about', 'more', 'home', 'through', 'where', 'should', 'because', 'does', 'most', 'while',
            'landfill', 'page', 'website', 'click', 'here', 'learn', 'read', 'visit'
        }
        
        # Count word frequency and filter business-relevant terms
        word_freq = {}
        for word in words:
            if (word not in stopwords and 
                len(word) > 3 and 
                word.isalpha() and
                not word.endswith(('ing', 'ed', 'er', 'est', 'ly'))):  # Filter common suffixes
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Prioritize business-relevant keywords
        business_keywords = []
        priority_terms = ['service', 'business', 'company', 'professional', 'commercial', 'industry', 'quality', 'expert']
        
        for word, freq in sorted(word_freq.items(), key=lambda x: x[1], reverse=True):
            if len(business_keywords) >= 8:
                break
            
            # Prioritize business terms
            if any(term in word for term in priority_terms):
                if word not in business_keywords:
                    business_keywords.insert(0, word)
            elif freq > 1 and word not in business_keywords:
                business_keywords.append(word)
        
        # Return top business keywords
        return business_keywords[:8] if business_keywords else ['professional', 'services', 'business', 'quality']
    
    def _extract_about_section(self, content: str) -> str:
        """Extract about/company description section"""
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            line_lower = line.lower().strip()
            if any(indicator in line_lower for indicator in ['about', 'company', 'who we are', 'our story', 'mission']):
                # Extract next few lines as about section
                about_lines = lines[i:i+5]
                about_text = ' '.join(about_lines).strip()
                if len(about_text) > 50:
                    return about_text[:500]  # Limit length
        
        # Fallback: take first substantial paragraph
        for line in lines:
            if len(line.strip()) > 100:
                return line.strip()[:500]
        
        return "Professional business services provider"
    
    def _extract_distinctives(self, content: str) -> List[str]:
        """Extract unique selling points and distinctives"""
        distinctives = []
        
        # Look for common distinctive patterns
        distinctive_patterns = [
            r'(\d+\+?\s*years?\s*(?:of\s*)?experience)',
            r'(licensed\s+(?:and\s+)?insured)',
            r'(free\s+(?:estimates?|quotes?))',
            r'(24/?7\s*(?:service|support|availability))',
            r'(award[- ]winning)',
            r'(certified\s+\w+)',
            r'(family[- ]owned)',
            r'(locally[- ]owned)',
            r'(satisfaction\s+guaranteed)',
            r'(same[- ]day\s+service)'
        ]
        
        content_lower = content.lower()
        for pattern in distinctive_patterns:
            matches = re.findall(pattern, content_lower)
            distinctives.extend(matches)
        
        # Look for quality indicators
        quality_terms = ['quality', 'professional', 'experienced', 'trusted', 'reliable', 'expert']
        for term in quality_terms:
            if term in content_lower and term not in distinctives:
                distinctives.append(f"{term} service")
        
        return distinctives[:8]  # Limit to top distinctives
    
    def _find_social_media_links(self, url: str, content: str) -> Dict[str, Any]:
        """Find social media profiles and links"""
        social_media = {
            'facebook': None,
            'instagram': None,
            'twitter': None,
            'linkedin': None,
            'youtube': None,
            'found_links': []
        }
        
        # Social media patterns
        social_patterns = {
            'facebook': [r'facebook\.com/[\w.-]+', r'fb\.me/[\w.-]+'],
            'instagram': [r'instagram\.com/[\w.-]+'],
            'twitter': [r'twitter\.com/[\w.-]+', r'x\.com/[\w.-]+'],
            'linkedin': [r'linkedin\.com/(?:company|in)/[\w.-]+'],
            'youtube': [r'youtube\.com/(?:channel|user|c)/[\w.-]+']
        }
        
        full_text = f"{url} {content}"
        
        for platform, patterns in social_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, full_text, re.IGNORECASE)
                if matches:
                    social_media[platform] = matches[0]
                    social_media['found_links'].append(matches[0])
        
        return social_media
    
    def _calculate_confidence_score(self, business_name: str, industry: str, 
                                   geography: Dict, keywords: List, about_section: str) -> float:
        """Calculate confidence score for the extracted profile"""
        score = 0.0
        
        # Business name quality (0-0.2)
        if business_name and len(business_name) > 3:
            score += 0.2
        
        # Industry classification (0-0.3)
        if industry != "professional_services":
            score += 0.3
        else:
            score += 0.1
        
        # Geographic information (0-0.2)
        if geography.get('state') or geography.get('city'):
            score += 0.2
        elif geography.get('indicators'):
            score += 0.1
        
        # Keywords quality (0-0.2)
        if len(keywords) >= 10:
            score += 0.2
        elif len(keywords) >= 5:
            score += 0.1
        
        # About section quality (0-0.1)
        if about_section and len(about_section) > 100:
            score += 0.1
        
        return min(score, 1.0)
    
    def _create_fallback_profile(self, url: str) -> SellProfile:
        """Create minimal profile when extraction fails"""
        domain = urlparse(url).netloc.replace('www.', '')
        business_name = domain.split('.')[0].replace('-', ' ').title()
        
        return SellProfile(
            url=url,
            business_name=business_name,
            industry="professional_services",
            geography={'country': 'US', 'indicators': []},
            metadata={'domain': domain, 'extracted_method': 'fallback'},
            keywords=['professional', 'services', 'business'],
            about_section="Professional business services provider",
            distinctives=['professional service', 'customer focused'],
            social_media={'found_links': []},
            extracted_at=datetime.now().isoformat(),
            confidence_score=0.3
        )
    
    def export_profile(self, profile: SellProfile) -> Dict[str, Any]:
        """Export profile as dictionary for API responses"""
        return asdict(profile)