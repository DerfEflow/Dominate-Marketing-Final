#!/usr/bin/env python3
"""
Quality assessment script for generated content
Tests content generation and provides detailed quality analysis
"""

import sys
import os
import asyncio
from datetime import datetime

# Add modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

from web_scraper import ReliableWebScraper
from ai_strategy_generator import AIStrategyGenerator
from content_generator import ContentGenerator

def analyze_content_quality(content_output):
    """Analyze quality of generated content"""
    quality_report = {
        'images': {'total': 0, 'successful': 0, 'quality_score': 0},
        'videos': {'total': 0, 'successful': 0, 'quality_score': 0}, 
        'texts': {'total': 0, 'successful': 0, 'quality_score': 0},
        'overall_quality': 0
    }
    
    # Analyze Images
    images = content_output.get('images', [])
    quality_report['images']['total'] = len(images)
    
    for img in images:
        if img.get('status') == 'success':
            quality_report['images']['successful'] += 1
            # Quality factors: has URL, good prompt, appropriate style
            score = 0
            if img.get('url'):
                score += 40
            if len(img.get('prompt_used', '')) > 20:
                score += 30
            if img.get('style') in ['professional', 'creative', 'modern']:
                score += 30
            quality_report['images']['quality_score'] += score
    
    if images:
        quality_report['images']['quality_score'] /= len(images)
    
    # Analyze Videos
    videos = content_output.get('videos', [])
    quality_report['videos']['total'] = len(videos)
    
    for vid in videos:
        if vid.get('status') in ['success', 'concept_ready']:
            quality_report['videos']['successful'] += 1
            # Quality factors: has concept, good duration, detailed description
            score = 0
            if len(vid.get('concept', '')) > 50:
                score += 40
            if vid.get('duration') in ['15s', '30s', '60s']:
                score += 30
            if len(vid.get('prompt_used', '')) > 20:
                score += 30
            quality_report['videos']['quality_score'] += score
    
    if videos:
        quality_report['videos']['quality_score'] /= len(videos)
    
    # Analyze Text Content
    texts = content_output.get('texts', [])
    quality_report['texts']['total'] = len(texts)
    
    for txt in texts:
        if txt.get('status') == 'success':
            quality_report['texts']['successful'] += 1
            # Quality factors: word count, appropriate tone, platform-specific
            score = 0
            word_count = txt.get('word_count', 0)
            if 20 <= word_count <= 200:  # Appropriate length
                score += 40
            if txt.get('tone') in ['professional', 'engaging', 'persuasive']:
                score += 30
            if txt.get('platform') in ['instagram', 'facebook', 'email', 'website']:
                score += 30
            quality_report['texts']['quality_score'] += score
    
    if texts:
        quality_report['texts']['quality_score'] /= len(texts)
    
    # Calculate overall quality
    scores = [
        quality_report['images']['quality_score'],
        quality_report['videos']['quality_score'],
        quality_report['texts']['quality_score']
    ]
    quality_report['overall_quality'] = sum(scores) / len([s for s in scores if s > 0]) if any(scores) else 0
    
    return quality_report

async def test_content_quality():
    """Test content generation and analyze quality"""
    print("🔍 CONTENT QUALITY ASSESSMENT")
    print("=" * 60)
    
    try:
        # Step 1: Extract business data
        print("1. Extracting business data...")
        scraper = ReliableWebScraper()
        business_data = scraper.extract_business_data("https://replit.com")
        
        print(f"   ✅ Business: {business_data['business_name']}")
        print(f"   ✅ Content: {business_data['content_length']} characters")
        
        # Step 2: Generate strategy
        print("\n2. Generating marketing strategy...")
        strategy_gen = AIStrategyGenerator()
        strategy = strategy_gen.generate_marketing_strategy(business_data, [])
        
        print(f"   ✅ Strategy model: {strategy.get('model_used', 'N/A')}")
        print(f"   ✅ Target audience: {strategy.get('target_audience', {}).get('primary', 'N/A')[:50]}...")
        
        # Step 3: Generate content prompts
        print("\n3. Generating content prompts...")
        prompts = strategy_gen.generate_content_prompts(strategy)
        
        img_count = len(prompts.get('image_prompts', []))
        vid_count = len(prompts.get('video_prompts', []))
        txt_count = len(prompts.get('text_prompts', []))
        
        print(f"   ✅ Generated {img_count} image prompts")
        print(f"   ✅ Generated {vid_count} video prompts")
        print(f"   ✅ Generated {txt_count} text prompts")
        
        # Step 4: Generate actual content
        print("\n4. Generating final content...")
        content_gen = ContentGenerator()
        content = content_gen.generate_all_content(prompts)
        
        summary = content.get('generation_summary', {})
        print(f"   ✅ Images: {summary.get('total_images', 0)}")
        print(f"   ✅ Videos: {summary.get('total_videos', 0)}")
        print(f"   ✅ Texts: {summary.get('total_texts', 0)}")
        
        # Step 5: Quality Analysis
        print("\n5. Analyzing content quality...")
        quality = analyze_content_quality(content)
        
        print(f"\n📊 QUALITY ASSESSMENT RESULTS")
        print("=" * 60)
        
        # Image Quality
        img_success_rate = (quality['images']['successful'] / quality['images']['total'] * 100) if quality['images']['total'] > 0 else 0
        print(f"📸 IMAGES:")
        print(f"   Success Rate: {img_success_rate:.1f}% ({quality['images']['successful']}/{quality['images']['total']})")
        print(f"   Quality Score: {quality['images']['quality_score']:.1f}/100")
        
        if content.get('images'):
            for img in content['images']:
                if img.get('status') == 'success':
                    print(f"   ✅ {img['title']}: {img.get('style', 'N/A')} style")
                    print(f"      URL: {img.get('url', 'N/A')[:50]}...")
                else:
                    print(f"   ❌ {img.get('title', 'Unknown')}: {img.get('error', 'Failed')}")
        
        # Video Quality
        vid_success_rate = (quality['videos']['successful'] / quality['videos']['total'] * 100) if quality['videos']['total'] > 0 else 0
        print(f"\n🎥 VIDEOS:")
        print(f"   Success Rate: {vid_success_rate:.1f}% ({quality['videos']['successful']}/{quality['videos']['total']})")
        print(f"   Quality Score: {quality['videos']['quality_score']:.1f}/100")
        
        if content.get('videos'):
            for vid in content['videos']:
                status = vid.get('status', 'unknown')
                print(f"   {'✅' if status in ['success', 'concept_ready'] else '❌'} {vid['title']}: {status}")
                print(f"      Duration: {vid.get('duration', 'N/A')}")
                if vid.get('concept'):
                    print(f"      Concept: {vid['concept'][:100]}...")
        
        # Text Quality
        txt_success_rate = (quality['texts']['successful'] / quality['texts']['total'] * 100) if quality['texts']['total'] > 0 else 0
        print(f"\n📝 TEXT CONTENT:")
        print(f"   Success Rate: {txt_success_rate:.1f}% ({quality['texts']['successful']}/{quality['texts']['total']})")
        print(f"   Quality Score: {quality['texts']['quality_score']:.1f}/100")
        
        if content.get('texts'):
            for txt in content['texts']:
                if txt.get('status') == 'success':
                    print(f"   ✅ {txt['title']}: {txt.get('word_count', 0)} words ({txt.get('platform', 'N/A')})")
                    print(f"      Content: {txt.get('content', 'N/A')[:80]}...")
                else:
                    print(f"   ❌ {txt.get('title', 'Unknown')}: {txt.get('error', 'Failed')}")
        
        # Overall Assessment
        print(f"\n🎯 OVERALL QUALITY SCORE: {quality['overall_quality']:.1f}/100")
        
        if quality['overall_quality'] >= 80:
            print("🎉 EXCELLENT QUALITY - Content is production ready")
        elif quality['overall_quality'] >= 60:
            print("✅ GOOD QUALITY - Content meets standards with minor improvements needed")
        elif quality['overall_quality'] >= 40:
            print("⚠️  MODERATE QUALITY - Content needs improvement before production")
        else:
            print("❌ LOW QUALITY - Significant improvements needed")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Quality assessment failed: {str(e)}")
        return False

def main():
    """Main quality test runner"""
    print("🎨 VISUAL CONTENT QUALITY TESTER")
    print("Testing all modules and analyzing output quality...")
    print()
    
    success = asyncio.run(test_content_quality())
    
    if success:
        print(f"\n✅ Quality assessment completed successfully!")
        print("\n💡 To run the visual interface:")
        print("   python run_visual_tester.py")
        print("   or")
        print("   python -m reflex run --app visual_tester:visual_app")
    else:
        print(f"\n❌ Quality assessment failed")
        print("Check API configuration and try again")

if __name__ == "__main__":
    main()