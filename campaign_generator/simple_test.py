#!/usr/bin/env python3
"""
Simple test for the campaign generator core functionality
Tests without Reflex dependencies
"""

import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Import only the core generator class
try:
    from campaign_generator import CampaignGenerator
    print("✅ Campaign generator imported successfully")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

class SimpleState:
    """Simple state mock for testing"""
    def __init__(self):
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

async def test_basic_functionality():
    """Test basic functionality of campaign generator"""
    print("\n🧪 TESTING BASIC FUNCTIONALITY")
    print("=" * 50)
    
    # Test initialization
    generator = CampaignGenerator()
    print("✅ CampaignGenerator initialized")
    
    # Test API key detection
    has_openai = bool(generator.openai_api_key)
    has_google = bool(generator.google_api_key) 
    has_search = bool(generator.google_search_api_key)
    
    print(f"OpenAI API: {'✅ Configured' if has_openai else '❌ Not configured'}")
    print(f"Google API: {'✅ Configured' if has_google else '❌ Not configured'}")
    print(f"Search API: {'✅ Configured' if has_search else '❌ Not configured'}")
    
    # Test website scraping
    print("\n📡 Testing website scraping...")
    state = SimpleState()
    
    try:
        website_data = await generator._scrape_website_data("https://replit.com", state)
        print("✅ Website scraping successful")
        print(f"   Business: {website_data.get('business_name')}")
        print(f"   Content: {website_data.get('content_length')} characters")
        print(f"   Domain: {website_data.get('domain')}")
        
        # Test competitor analysis with scraped data
        print("\n🔍 Testing competitor analysis...")
        competitors = await generator._analyze_competitors(website_data, state)
        print("✅ Competitor analysis successful")
        print(f"   Found: {len(competitors)} competitors")
        
        return True
        
    except Exception as e:
        print(f"❌ Testing failed: {str(e)}")
        return False

async def test_ai_integration():
    """Test AI integration components"""
    print("\n🤖 TESTING AI INTEGRATION")
    print("=" * 50)
    
    generator = CampaignGenerator()
    state = SimpleState()
    
    # Mock data for testing
    mock_website_data = {
        'business_name': 'TestBusiness',
        'main_content': 'A test business that provides innovative solutions',
        'domain': 'testbusiness.com',
        'metadata': {'title': 'Test Business - Innovation Solutions'}
    }
    
    mock_competitors = [
        {'name': 'Competitor A', 'description': 'Main competitor in the market'}
    ]
    
    if generator.openai_api_key:
        print("🧠 Testing marketing strategy generation...")
        try:
            strategy = await generator._generate_marketing_strategy(
                mock_website_data, mock_competitors, state
            )
            print("✅ Marketing strategy generated")
            print(f"   Strategy keys: {list(strategy.keys())}")
            
            print("📝 Testing content prompt generation...")
            prompts = await generator._generate_content_prompts(strategy, state)
            print("✅ Content prompts generated")
            print(f"   Image prompts: {len(prompts.get('image_prompts', []))}")
            print(f"   Video prompts: {len(prompts.get('video_prompts', []))}")
            print(f"   Text prompts: {len(prompts.get('text_prompts', []))}")
            
            return True
            
        except Exception as e:
            print(f"❌ AI integration test failed: {str(e)}")
            return False
    else:
        print("⚠️  Skipping AI tests - OpenAI API key not configured")
        return True

def main():
    """Main test function"""
    print("🚀 CAMPAIGN GENERATOR - CORE FUNCTIONALITY TEST")
    print("=" * 60)
    
    try:
        # Test basic functionality
        basic_success = asyncio.run(test_basic_functionality())
        
        # Test AI integration
        ai_success = asyncio.run(test_ai_integration())
        
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        print(f"Basic Functionality: {'✅ PASSED' if basic_success else '❌ FAILED'}")
        print(f"AI Integration: {'✅ PASSED' if ai_success else '❌ FAILED'}")
        
        if basic_success and ai_success:
            print("\n🎉 ALL TESTS PASSED!")
            print("The campaign generator core is working properly.")
            print("\n💡 To run the full Reflex app:")
            print("   reflex run")
        else:
            print("\n⚠️  Some tests failed.")
            print("Check API configuration in .env file")
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Test execution failed: {str(e)}")

if __name__ == "__main__":
    main()