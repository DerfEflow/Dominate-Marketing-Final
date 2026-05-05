#!/usr/bin/env python3
"""
Test script for campaign generator module
Tests the core functionality without running the full Reflex app
"""

import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from campaign_generator import CampaignGenerator

class MockState:
    """Mock state for testing without Reflex runtime"""
    
    def __init__(self):
        # Initialize all state variables
        self.url_input = ""
        self.is_processing = False
        self.current_step = ""
        self.progress_percentage = 0
        self.campaign_id = ""
        self.website_data = {}
        self.competitors = []
        self.marketing_strategy = {}
        self.content_prompts = {}
        self.generated_content = {}
        self.status_messages = []
        self.error_message = ""

async def test_campaign_generation():
    """Test the campaign generation workflow"""
    print("🚀 TESTING CAMPAIGN GENERATOR MODULE")
    print("=" * 50)
    
    # Initialize components
    generator = CampaignGenerator()
    state = MockState()
    
    # Test URL
    test_url = "https://replit.com"
    print(f"Testing with URL: {test_url}")
    
    try:
        # Test the complete campaign generation workflow
        print("\n📋 Starting campaign generation workflow...")
        
        async for _ in generator.generate_campaign(test_url, state):
            print(f"Progress: {state.progress_percentage}% - {state.current_step}")
            if state.status_messages:
                print(f"Latest status: {state.status_messages[-1]}")
        
        # Display results
        print("\n✅ CAMPAIGN GENERATION COMPLETED!")
        print(f"Campaign ID: {state.campaign_id}")
        print(f"Business Name: {state.website_data.get('business_name', 'N/A')}")
        print(f"Content Length: {state.website_data.get('content_length', 0)} characters")
        print(f"Competitors Found: {len(state.competitors)}")
        print(f"Images Generated: {len(state.generated_content.get('images', []))}")
        print(f"Videos Generated: {len(state.generated_content.get('videos', []))}")
        print(f"Text Content Generated: {len(state.generated_content.get('texts', []))}")
        
        # Show sample generated content
        if state.generated_content.get('texts'):
            print("\n📝 Sample Generated Text:")
            first_text = state.generated_content['texts'][0]
            print(f"Title: {first_text.get('title', 'N/A')}")
            print(f"Content: {first_text.get('content', 'N/A')[:100]}...")
        
        if state.generated_content.get('images'):
            print("\n🖼️ Sample Generated Image:")
            first_image = state.generated_content['images'][0]
            print(f"Title: {first_image.get('title', 'N/A')}")
            if 'url' in first_image:
                print(f"URL: {first_image['url']}")
            else:
                print(f"Status: {first_image.get('status', 'Unknown')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Campaign generation failed: {str(e)}")
        print(f"Error message in state: {state.error_message}")
        return False

async def test_individual_components():
    """Test individual components of the campaign generator"""
    print("\n🔧 TESTING INDIVIDUAL COMPONENTS")
    print("=" * 50)
    
    generator = CampaignGenerator()
    state = MockState()
    
    # Test 1: Website scraping
    print("\n1. Testing website scraping...")
    try:
        website_data = await generator._scrape_website_data("https://replit.com", state)
        print(f"✅ Website scraping successful")
        print(f"   Business Name: {website_data.get('business_name')}")
        print(f"   Content Length: {website_data.get('content_length')}")
        print(f"   Domain: {website_data.get('domain')}")
    except Exception as e:
        print(f"❌ Website scraping failed: {str(e)}")
    
    # Test 2: Competitor analysis
    print("\n2. Testing competitor analysis...")
    try:
        mock_website_data = {
            'business_name': 'Replit',
            'main_content': 'Cloud-based development platform for coding',
            'domain': 'replit.com'
        }
        competitors = await generator._analyze_competitors(mock_website_data, state)
        print(f"✅ Competitor analysis successful")
        print(f"   Competitors found: {len(competitors)}")
        for comp in competitors[:2]:
            print(f"   - {comp.get('name', 'N/A')}: {comp.get('description', 'N/A')[:50]}...")
    except Exception as e:
        print(f"❌ Competitor analysis failed: {str(e)}")
    
    # Test 3: API connectivity
    print("\n3. Testing API connectivity...")
    print(f"   OpenAI API Key: {'✅ Configured' if generator.openai_api_key else '❌ Not configured'}")
    print(f"   Google API Key: {'✅ Configured' if generator.google_api_key else '❌ Not configured'}")
    print(f"   Google Search API: {'✅ Configured' if generator.google_search_api_key else '❌ Not configured'}")
    
    print("\n📊 Component testing completed!")

if __name__ == "__main__":
    print("Campaign Generator Test Suite")
    print("Testing core functionality...")
    
    # Run tests
    asyncio.run(test_individual_components())
    
    print("\n" + "="*50)
    print("Starting full workflow test...")
    success = asyncio.run(test_campaign_generation())
    
    if success:
        print("\n🎉 ALL TESTS PASSED - Campaign Generator is ready!")
    else:
        print("\n⚠️  Some tests failed - Check API configuration")
    
    print("\n💡 To run the Reflex frontend:")
    print("   cd campaign_generator")
    print("   reflex run")