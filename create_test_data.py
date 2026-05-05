"""
Create test data for dashboard demonstration
"""
import os
import sys
from datetime import datetime, timedelta
import json

# Add the current directory to Python path
sys.path.append('.')

from main_app import create_app
from models import db, User, Brand, Campaign, SocialPost, SubscriptionTier

def create_test_data():
    """Create comprehensive test data for dashboard demonstration"""
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
                'description': 'Innovative software solutions for modern businesses. We specialize in AI-powered automation and cloud infrastructure.',
                'subscription_tier': SubscriptionTier.PRO
            },
            {
                'name': 'Green Earth Cafe',
                'website_url': 'https://greenearthcafe.example.com',
                'industry': 'Food & Beverage',
                'description': 'Sustainable coffee shop chain focused on organic, fair-trade products and eco-friendly practices.',
                'subscription_tier': SubscriptionTier.BASIC
            },
            {
                'name': 'FitLife Gym',
                'website_url': 'https://fitlifegym.example.com',
                'industry': 'Fitness',
                'description': 'Premium fitness center offering personal training, group classes, and cutting-edge equipment.',
                'subscription_tier': SubscriptionTier.PLUS
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
        
        # Create test campaigns with rich content
        campaigns_data = [
            {
                'brand': created_brands[0],  # TechFlow Solutions
                'title': 'AI Product Launch Campaign',
                'business_url': 'https://techflow.example.com/ai-assistant',
                'target_audience': 'Tech-savvy business owners',
                'campaign_goal': 'product_launch',
                'brand_voice': 'professional',
                'status': 'completed',
                'quality_score': 89,
                'ai_content': {
                    'images': [
                        {
                            'id': 1,
                            'title': 'AI Assistant Hero Image',
                            'url': 'https://images.unsplash.com/photo-1677442136019-21780ecad995?w=800',
                            'platform': 'instagram',
                            'regeneration_count': 0
                        },
                        {
                            'id': 2,
                            'title': 'Product Dashboard Screenshot',
                            'url': 'https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=800',
                            'platform': 'linkedin',
                            'regeneration_count': 1
                        }
                    ],
                    'videos': [
                        {
                            'id': 3,
                            'title': 'AI Demo Video Concept',
                            'concept': 'Professional screen recording showing AI assistant in action with smooth transitions',
                            'platform': 'youtube',
                            'regeneration_count': 0
                        }
                    ],
                    'texts': [
                        {
                            'id': 4,
                            'title': 'Instagram Post Copy',
                            'content': '🚀 Revolutionize your workflow with our new AI Assistant! \n\n✨ Automate repetitive tasks\n📊 Get intelligent insights\n⚡ Boost productivity by 40%\n\nJoin 10,000+ businesses already transforming their operations. Link in bio! #AI #Productivity #Innovation',
                            'platform': 'instagram',
                            'regeneration_count': 0
                        },
                        {
                            'id': 5,
                            'title': 'LinkedIn Article',
                            'content': 'The Future of Business Automation is Here\n\nAfter 2 years of development, we\'re excited to announce our AI Assistant that\'s already helping businesses save 15+ hours per week. Unlike generic tools, our solution learns your specific workflows and adapts to your industry needs.\n\nKey benefits our beta users are seeing:\n• 40% reduction in manual data entry\n• Intelligent task prioritization\n• Seamless integration with existing tools\n\nReady to transform your business operations? Schedule a demo today.',
                            'platform': 'linkedin',
                            'regeneration_count': 2
                        }
                    ]
                }
            },
            {
                'brand': created_brands[1],  # Green Earth Cafe
                'title': 'Summer Menu Promotion',
                'business_url': 'https://greenearthcafe.example.com/summer-menu',
                'target_audience': 'Health-conscious coffee lovers',
                'campaign_goal': 'sales_boost',
                'brand_voice': 'friendly',
                'status': 'completed',
                'quality_score': 92,
                'ai_content': {
                    'images': [
                        {
                            'id': 6,
                            'title': 'Summer Cold Brew Collection',
                            'url': 'https://images.unsplash.com/photo-1461023058943-07fcbe16d735?w=800',
                            'platform': 'facebook',
                            'regeneration_count': 0
                        },
                        {
                            'id': 7,
                            'title': 'Fresh Smoothie Bowl',
                            'url': 'https://images.unsplash.com/photo-1511690743698-d9d85f2fbf38?w=800',
                            'platform': 'instagram',
                            'regeneration_count': 0
                        }
                    ],
                    'texts': [
                        {
                            'id': 8,
                            'title': 'Facebook Summer Menu Post',
                            'content': '☀️ Beat the heat with our NEW Summer Menu! ☀️\n\nIntroducing refreshing cold brews, tropical smoothie bowls, and organic iced teas that will keep you cool and energized all season long.\n\n🌱 100% organic ingredients\n☕ Fair-trade certified coffee\n🥤 Dairy-free options available\n\nVisit us today and taste the difference! What\'s your favorite summer drink? Let us know in the comments! 👇',
                            'platform': 'facebook',
                            'regeneration_count': 1
                        }
                    ]
                }
            },
            {
                'brand': created_brands[2],  # FitLife Gym
                'title': 'New Year Fitness Challenge',
                'business_url': 'https://fitlifegym.example.com/new-year-challenge',
                'target_audience': 'Fitness enthusiasts and beginners',
                'campaign_goal': 'membership_drive',
                'brand_voice': 'motivational',
                'status': 'processing',
                'quality_score': 85,
                'ai_content': {
                    'images': [
                        {
                            'id': 9,
                            'title': 'Gym Equipment Showcase',
                            'url': 'https://images.unsplash.com/photo-1534438327276-14e5300c3a48?w=800',
                            'platform': 'instagram',
                            'regeneration_count': 0
                        }
                    ],
                    'texts': [
                        {
                            'id': 10,
                            'title': 'Instagram Challenge Announcement',
                            'content': '💪 NEW YEAR, NEW YOU CHALLENGE! 💪\n\n🎯 28-day transformation program\n👨‍💼 Personal trainer included\n📊 Progress tracking & nutrition guide\n🏆 Win amazing prizes!\n\nSpecial offer: 50% off first month for new members! \n\nTag 3 friends who need to see this! 👇\n#NewYearNewYou #FitnessChallenge #FitLife',
                            'platform': 'instagram',
                            'regeneration_count': 0
                        }
                    ]
                }
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
                    ai_content=json.dumps(camp_data['ai_content']),
                    tier_used='pro',
                    created_at=datetime.now() - timedelta(days=15),
                    completed_at=datetime.now() - timedelta(days=5) if camp_data['status'] == 'completed' else None
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
                'content': '🚀 Revolutionize your workflow with our new AI Assistant! Link in bio! #AI #Productivity',
                'scheduled_time': datetime.now() + timedelta(hours=2),
                'status': 'scheduled'
            },
            {
                'campaign': created_campaigns[0],
                'platform': 'linkedin',
                'content': 'The Future of Business Automation is Here. Schedule a demo today.',
                'scheduled_time': datetime.now() + timedelta(days=1),
                'status': 'scheduled'
            },
            {
                'campaign': created_campaigns[1],
                'platform': 'facebook',
                'content': '☀️ Beat the heat with our NEW Summer Menu! 100% organic ingredients.',
                'scheduled_time': datetime.now() - timedelta(days=2),
                'status': 'posted',
                'posted_at': datetime.now() - timedelta(days=2)
            },
            {
                'campaign': created_campaigns[2],
                'platform': 'instagram',
                'content': '💪 NEW YEAR, NEW YOU CHALLENGE! 28-day transformation program starts Monday!',
                'scheduled_time': datetime.now() + timedelta(days=3),
                'status': 'scheduled'
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
                    scheduled_time=post_data['scheduled_time'],
                    status=post_data['status'],
                    posted_at=post_data.get('posted_at'),
                    created_at=datetime.now() - timedelta(days=10)
                )
                db.session.add(post)
                created_posts += 1
        
        db.session.commit()
        print(f"Created {created_posts} scheduled social posts")
        
        print("\n✅ Test data creation complete!")
        print(f"Demo login credentials:")
        print(f"Email: demo@dominatemarketing.com")
        print(f"User ID: {test_user.id}")
        print(f"\nDashboard features demonstrated:")
        print(f"• {len(created_brands)} brands with different subscription tiers")
        print(f"• {len(created_campaigns)} campaigns with various statuses")
        print(f"• Rich AI-generated content (images, videos, texts)")
        print(f"• {created_posts} scheduled social media posts")
        print(f"• Quality scores and regeneration tracking")
        
        return test_user

if __name__ == '__main__':
    create_test_data()