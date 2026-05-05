"""
Create simple test data for dashboard demonstration
"""
import os
import sys
from datetime import datetime, timedelta
import json

# Add the current directory to Python path
sys.path.append('.')

from main_app import create_app
from models import db, User, Brand, Campaign, SocialPost, SubscriptionTier

def create_simple_test_data():
    """Create basic test data for dashboard demonstration"""
    app = create_app()
    
    with app.app_context():
        # Create test user
        test_user = User.query.filter_by(email='demo@dominatemarketing.com').first()
        if not test_user:
            test_user = User(
                email='demo@dominatemarketing.com',
                username='Demo User',
                full_name='Marketing Demo Account',
                subscription_tier=SubscriptionTier.PRO,
                subscription_expires=datetime.now() + timedelta(days=365),
                account_active=True,
                is_demo_account=True
            )
            db.session.add(test_user)
            db.session.commit()
            print(f"Created test user: {test_user.email}")
        
        # Create test brands
        brands_data = [
            {
                'name': 'TechFlow Solutions',
                'website_url': 'https://techflow.example.com',
                'industry': 'Technology',
                'description': 'Innovative software solutions for modern businesses.',
                'subscription_tier': SubscriptionTier.PRO
            },
            {
                'name': 'Green Earth Cafe',
                'website_url': 'https://greenearthcafe.example.com',
                'industry': 'Food & Beverage',
                'description': 'Sustainable coffee shop chain focused on organic products.',
                'subscription_tier': SubscriptionTier.BASIC
            }
        ]
        
        created_brands = []
        for brand_data in brands_data:
            existing_brand = Brand.query.filter_by(name=brand_data['name'], user_id=test_user.id).first()
            if not existing_brand:
                brand = Brand(
                    user_id=test_user.id,
                    name=brand_data['name'],
                    website_url=brand_data['website_url'],
                    industry=brand_data['industry'],
                    description=brand_data['description'],
                    subscription_tier=brand_data['subscription_tier'],
                    subscription_expires=datetime.now() + timedelta(days=365),
                    is_active=True,
                    created_at=datetime.now() - timedelta(days=30)
                )
                db.session.add(brand)
                created_brands.append(brand)
            else:
                created_brands.append(existing_brand)
        
        db.session.commit()
        print(f"Created {len(created_brands)} test brands")
        
        # Create test campaigns with simple AI content
        ai_content_sample = {
            'images': [
                {'title': 'Hero Image', 'url': 'https://images.unsplash.com/photo-1677442136019-21780ecad995?w=800', 'platform': 'instagram'},
                {'title': 'Product Image', 'url': 'https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=800', 'platform': 'facebook'}
            ],
            'texts': [
                {'title': 'Instagram Post', 'content': 'Check out our amazing new product! #innovation #tech', 'platform': 'instagram'},
                {'title': 'Facebook Post', 'content': 'Exciting news! Our latest solution is here to transform your business.', 'platform': 'facebook'}
            ],
            'videos': [
                {'title': 'Demo Video', 'concept': 'Professional product demonstration with smooth transitions', 'platform': 'youtube'}
            ]
        }
        
        campaigns_data = [
            {
                'brand': created_brands[0],
                'title': 'AI Product Launch',
                'business_url': 'https://techflow.example.com/ai-assistant',
                'target_audience': 'Tech-savvy business owners',
                'campaign_goal': 'product_launch',
                'brand_voice': 'professional',
                'status': 'completed',
                'quality_score': 8,  # Using scale 1-10 instead of 1-100
                'ai_content': json.dumps(ai_content_sample)
            },
            {
                'brand': created_brands[1],
                'title': 'Summer Menu Promotion',
                'business_url': 'https://greenearthcafe.example.com/summer-menu',
                'target_audience': 'Health-conscious coffee lovers',
                'campaign_goal': 'sales_boost',
                'brand_voice': 'friendly',
                'status': 'completed',
                'quality_score': 9,
                'ai_content': json.dumps({
                    'images': [{'title': 'Summer Drinks', 'url': 'https://images.unsplash.com/photo-1461023058943-07fcbe16d735?w=800', 'platform': 'instagram'}],
                    'texts': [{'title': 'Summer Menu Post', 'content': 'Beat the heat with our refreshing summer menu! ☀️', 'platform': 'facebook'}]
                })
            }
        ]
        
        created_campaigns = []
        for camp_data in campaigns_data:
            existing_campaign = Campaign.query.filter_by(title=camp_data['title'], user_id=test_user.id).first()
            if not existing_campaign:
                campaign = Campaign(
                    user_id=test_user.id,
                    brand_id=camp_data['brand'].id,
                    title=camp_data['title'],
                    business_url=camp_data['business_url'],
                    target_audience=camp_data['target_audience'],
                    campaign_goal=camp_data['campaign_goal'],
                    brand_voice=camp_data['brand_voice'],
                    status=camp_data['status'],
                    quality_score=camp_data['quality_score'],
                    ai_content=camp_data['ai_content'],
                    tier_used='pro',
                    created_at=datetime.now() - timedelta(days=15),
                    completed_at=datetime.now() - timedelta(days=5)
                )
                db.session.add(campaign)
                created_campaigns.append(campaign)
            else:
                created_campaigns.append(existing_campaign)
        
        db.session.commit()
        print(f"Created {len(created_campaigns)} test campaigns")
        
        # Create scheduled social posts
        posts_data = [
            {
                'campaign': created_campaigns[0],
                'platform': 'instagram',
                'content': 'Check out our amazing new AI product! #innovation #tech',
                'scheduled_for': datetime.now() + timedelta(hours=2),
                'status': 'scheduled'
            },
            {
                'campaign': created_campaigns[0],
                'platform': 'linkedin',
                'content': 'Transform your business with our AI solution. Schedule a demo today.',
                'scheduled_for': datetime.now() + timedelta(days=1),
                'status': 'scheduled'
            },
            {
                'campaign': created_campaigns[1],
                'platform': 'facebook',
                'content': 'Beat the heat with our refreshing summer menu! ☀️',
                'scheduled_for': datetime.now() - timedelta(days=2),
                'status': 'posted',
                'posted_at': datetime.now() - timedelta(days=2)
            }
        ]
        
        created_posts = 0
        for post_data in posts_data:
            existing_post = SocialPost.query.filter_by(
                campaign_id=post_data['campaign'].id,
                platform=post_data['platform']
            ).first()
            if not existing_post:
                post = SocialPost(
                    user_id=test_user.id,
                    campaign_id=post_data['campaign'].id,
                    platform=post_data['platform'],
                    content=post_data['content'],
                    scheduled_for=post_data['scheduled_for'],
                    status=post_data['status'],
                    posted_at=post_data.get('posted_at')
                )
                db.session.add(post)
                created_posts += 1
        
        db.session.commit()
        print(f"Created {created_posts} scheduled social posts")
        
        print("\n✅ Test data creation complete!")
        print(f"Demo login: /demo-login")
        print(f"Dashboard: /dashboard")
        print(f"\nDashboard features:")
        print(f"• {len(created_brands)} brands with different tiers")
        print(f"• {len(created_campaigns)} campaigns with AI content")
        print(f"• {created_posts} scheduled social posts")
        print(f"• Quality scoring and content management")
        
        return test_user

if __name__ == '__main__':
    create_simple_test_data()