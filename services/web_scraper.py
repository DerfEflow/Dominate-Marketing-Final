import requests
import trafilatura
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
import json
from typing import Dict, List, Optional
from datetime import datetime

def scrape_business_data(url: str) -> Dict:
    """
    Comprehensive business website scraping to extract metadata, keywords,
    products/services, and differentiating factors.
    """
    try:
        # Fetch the webpage
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Extract main text content using trafilatura
        downloaded = trafilatura.fetch_url(url)
        main_text = trafilatura.extract(downloaded) or ""
        
        # Parse HTML with BeautifulSoup for metadata
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract metadata
        metadata = extract_metadata(soup)
        
        # Extract keywords and key phrases
        keywords = extract_keywords(main_text, soup)
        
        # Identify products/services
        products_services = identify_products_services(main_text)
        
        # Find differentiators
        differentiators = find_differentiators(main_text)
        
        # Extract contact and business info
        business_info = extract_business_info(main_text, soup)
        
        return {
            'url': url,
            'title': metadata.get('title', ''),
            'description': metadata.get('description', ''),
            'keywords': keywords,
            'main_text': main_text[:2000],  # Truncate for storage
            'metadata': metadata,
            'products_services': products_services,
            'differentiators': differentiators,
            'business_info': business_info,
            'content_length': len(main_text),
            'scraped_at': str(datetime.utcnow())
        }
        
    except Exception as e:
        return {
            'url': url,
            'error': str(e),
            'scraped_at': str(datetime.utcnow())
        }

def extract_metadata(soup: BeautifulSoup) -> Dict:
    """Extract page metadata including title, description, and Open Graph data."""
    metadata = {}
    
    # Basic metadata
    if soup.title:
        metadata['title'] = soup.title.string.strip()
    
    # Description
    desc_meta = soup.find('meta', attrs={'name': 'description'})
    if desc_meta:
        metadata['description'] = desc_meta.get('content', '').strip()
    
    # Open Graph data
    og_tags = soup.find_all('meta', attrs={'property': re.compile(r'^og:')})
    for tag in og_tags:
        property_name = tag.get('property', '').replace('og:', '')
        metadata[f'og_{property_name}'] = tag.get('content', '').strip()
    
    # Twitter Card data
    twitter_tags = soup.find_all('meta', attrs={'name': re.compile(r'^twitter:')})
    for tag in twitter_tags:
        name = tag.get('name', '').replace('twitter:', '')
        metadata[f'twitter_{name}'] = tag.get('content', '').strip()
    
    # Keywords
    keywords_meta = soup.find('meta', attrs={'name': 'keywords'})
    if keywords_meta:
        metadata['meta_keywords'] = keywords_meta.get('content', '').strip()
    
    return metadata

def extract_keywords(text: str, soup: BeautifulSoup) -> List[str]:
    """Extract important keywords and phrases from the content."""
    keywords = set()
    
    # Extract from headings (higher weight)
    headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
    for heading in headings:
        if heading.text:
            keywords.update(extract_phrases(heading.text.strip()))
    
    # Extract from main content
    if text:
        # Look for emphasized text
        emphasized = soup.find_all(['strong', 'b', 'em', 'i'])
        for emp in emphasized:
            if emp.text:
                keywords.update(extract_phrases(emp.text.strip()))
        
        # Extract key phrases from full text
        keywords.update(extract_phrases(text))
    
    # Filter and return top keywords
    filtered_keywords = [kw for kw in keywords if len(kw) > 2 and len(kw.split()) <= 4]
    return sorted(list(set(filtered_keywords)))[:50]  # Top 50 keywords

def extract_phrases(text: str) -> List[str]:
    """Extract meaningful phrases from text."""
    # Simple phrase extraction - look for noun phrases and key terms
    words = re.findall(r'\b[A-Za-z]{3,}\b', text.lower())
    phrases = []
    
    # Single important words
    important_words = [w for w in words if len(w) >= 4]
    phrases.extend(important_words[:20])
    
    # Two-word phrases
    for i in range(len(words) - 1):
        phrase = f"{words[i]} {words[i+1]}"
        if len(phrase) >= 6:
            phrases.append(phrase)
    
    return phrases

def identify_products_services(text: str) -> List[str]:
    """Identify products and services mentioned in the content."""
    products_services = []
    
    # Look for common product/service indicators
    indicators = [
        r'we offer\s+([^.!?]+)',
        r'our services include\s+([^.!?]+)',
        r'we provide\s+([^.!?]+)',
        r'specializing in\s+([^.!?]+)',
        r'products:\s*([^.!?]+)',
        r'services:\s*([^.!?]+)',
    ]
    
    for pattern in indicators:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            products_services.append(match.strip())
    
    return products_services[:10]  # Top 10 products/services

def find_differentiators(text: str) -> List[str]:
    """Find what makes the business unique or different."""
    differentiators = []
    
    # Look for differentiation language
    diff_patterns = [
        r'unlike\s+([^.!?]+)',
        r'only\s+([^.!?]+)',
        r'first\s+([^.!?]+)',
        r'unique\s+([^.!?]+)',
        r'exclusively\s+([^.!?]+)',
        r'pioneering\s+([^.!?]+)',
        r'#1\s+([^.!?]+)',
        r'leading\s+([^.!?]+)',
        r'award[- ]winning\s+([^.!?]+)',
    ]
    
    for pattern in diff_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            differentiators.append(match.strip())
    
    return differentiators[:8]  # Top 8 differentiators

def extract_business_info(text: str, soup: BeautifulSoup) -> Dict:
    """Extract business contact and location information."""
    business_info = {}
    
    # Look for phone numbers
    phone_pattern = r'[\(]?[\d]{3}[\)]?[-.\s]?[\d]{3}[-.\s]?[\d]{4}'
    phones = re.findall(phone_pattern, text)
    if phones:
        business_info['phone'] = phones[0]
    
    # Look for email addresses
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text)
    if emails:
        business_info['email'] = emails[0]
    
    # Look for addresses (simple pattern)
    address_patterns = [
        r'\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd)',
        r'\d+\s+[A-Za-z\s]+,\s*[A-Za-z\s]+,\s*[A-Z]{2}\s+\d{5}'
    ]
    
    for pattern in address_patterns:
        addresses = re.findall(pattern, text, re.IGNORECASE)
        if addresses:
            business_info['address'] = addresses[0]
            break
    
    return business_info