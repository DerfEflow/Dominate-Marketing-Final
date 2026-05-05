"""
Social Media Integration Service
Handles posting to Facebook, Instagram, X, TikTok, and LinkedIn
"""

import logging
import requests
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from models import SocialAccount, SocialPost, SubscriptionTier

logger = logging.getLogger(__name__)

class SocialMediaService:
    """Service for social media platform integrations"""
    
    def __init__(self):
        self.supported_platforms = ['facebook', 'instagram', 'twitter', 'tiktok', 'linkedin']
        self.platform_configs = self._get_platform_configs()
    
    def get_user_accounts(self, user_id: str) -> List[SocialAccount]:
        """Get user's connected social media accounts"""
        return SocialAccount.query.filter_by(user_id=user_id, is_active=True).all()
    
    def connect_account(self, user_id: str, platform: str, auth_data: Dict[str, Any]) -> SocialAccount:
        """Connect a new social media account"""
        
        # Check if account already exists
        existing = SocialAccount.query.filter_by(
            user_id=user_id, 
            platform=platform,
            platform_user_id=auth_data.get('user_id')
        ).first()
        
        if existing:
            # Update existing account
            existing.access_token = auth_data.get('access_token')
            existing.refresh_token = auth_data.get('refresh_token')
            existing.token_expires = auth_data.get('expires_at')
            existing.username = auth_data.get('username')
            existing.is_active = True
            return existing
        else:
            # Create new account
            account = SocialAccount()
            account.user_id = user_id
            account.platform = platform
            account.platform_user_id = auth_data.get('user_id')
            account.username = auth_data.get('username')
            account.access_token = auth_data.get('access_token')
            account.refresh_token = auth_data.get('refresh_token')
            account.token_expires = auth_data.get('expires_at')
            account.is_active = True
            
            from models import db
            db.session.add(account)
            db.session.commit()
            
            return account
    
    def post_to_platform(self, social_post: SocialPost) -> Dict[str, Any]:
        """Post content to a specific platform"""
        
        # Get user's account for this platform
        account = SocialAccount.query.filter_by(
            user_id=social_post.user_id,
            platform=social_post.platform,
            is_active=True
        ).first()
        
        if not account:
            return {
                'success': False,
                'error': f'No connected {social_post.platform} account found'
            }
        
        # Check token expiry
        if account.token_expires and datetime.utcnow() > account.token_expires:
            refresh_result = self._refresh_token(account)
            if not refresh_result['success']:
                return {
                    'success': False,
                    'error': 'Failed to refresh access token'
                }
        
        # Post to platform
        try:
            platform_method = getattr(self, f'_post_to_{social_post.platform}')
            result = platform_method(account, social_post)
            
            if result['success']:
                social_post.status = 'posted'
                social_post.posted_at = datetime.utcnow()
                social_post.platform_post_id = result.get('post_id')
            else:
                social_post.status = 'failed'
                social_post.error_message = result.get('error')
            
            from models import db
            db.session.commit()
            
            return result
            
        except Exception as e:
            logger.error(f"Error posting to {social_post.platform}: {str(e)}")
            social_post.status = 'failed'
            social_post.error_message = str(e)
            
            from models import db
            db.session.commit()
            
            return {
                'success': False,
                'error': str(e)
            }
    
    def _post_to_facebook(self, account: SocialAccount, post: SocialPost) -> Dict[str, Any]:
        """Post to Facebook"""
        
        url = f"https://graph.facebook.com/me/feed"
        
        data = {
            'message': post.content,
            'access_token': account.access_token
        }
        
        # Add media if available
        if post.image_url:
            # For images, use different endpoint
            url = f"https://graph.facebook.com/me/photos"
            data['url'] = post.image_url
            data['caption'] = post.content
            del data['message']
        
        response = requests.post(url, data=data)
        
        if response.status_code == 200:
            result = response.json()
            return {
                'success': True,
                'post_id': result.get('id'),
                'platform_response': result
            }
        else:
            return {
                'success': False,
                'error': f"Facebook API error: {response.text}"
            }
    
    def _post_to_instagram(self, account: SocialAccount, post: SocialPost) -> Dict[str, Any]:
        """Post to Instagram"""
        
        # Instagram requires media (image or video)
        if not post.image_url and not post.video_url:
            return {
                'success': False,
                'error': 'Instagram posts require media (image or video)'
            }
        
        # Step 1: Create media object
        media_url = post.image_url or post.video_url
        media_type = 'IMAGE' if post.image_url else 'VIDEO'
        
        create_url = f"https://graph.facebook.com/v18.0/{account.platform_user_id}/media"
        create_data = {
            f'{media_type.lower()}_url': media_url,
            'caption': post.content,
            'access_token': account.access_token
        }
        
        create_response = requests.post(create_url, data=create_data)
        
        if create_response.status_code != 200:
            return {
                'success': False,
                'error': f"Instagram media creation error: {create_response.text}"
            }
        
        media_id = create_response.json()['id']
        
        # Step 2: Publish media
        publish_url = f"https://graph.facebook.com/v18.0/{account.platform_user_id}/media_publish"
        publish_data = {
            'creation_id': media_id,
            'access_token': account.access_token
        }
        
        publish_response = requests.post(publish_url, data=publish_data)
        
        if publish_response.status_code == 200:
            result = publish_response.json()
            return {
                'success': True,
                'post_id': result.get('id'),
                'platform_response': result
            }
        else:
            return {
                'success': False,
                'error': f"Instagram publish error: {publish_response.text}"
            }
    
    def _post_to_twitter(self, account: SocialAccount, post: SocialPost) -> Dict[str, Any]:
        """Post to X (Twitter)"""
        
        url = "https://api.twitter.com/2/tweets"
        
        headers = {
            'Authorization': f'Bearer {account.access_token}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'text': post.content
        }
        
        # Add media if available
        if post.image_url:
            # Note: Media upload requires separate endpoint and process
            # This is a simplified version
            data['media'] = {'media_ids': []}  # Would need to upload media first
        
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 201:
            result = response.json()
            return {
                'success': True,
                'post_id': result['data']['id'],
                'platform_response': result
            }
        else:
            return {
                'success': False,
                'error': f"Twitter API error: {response.text}"
            }
    
    def _post_to_tiktok(self, account: SocialAccount, post: SocialPost) -> Dict[str, Any]:
        """Post to TikTok"""
        
        # TikTok requires video content
        if not post.video_url:
            return {
                'success': False,
                'error': 'TikTok posts require video content'
            }
        
        # TikTok API implementation would go here
        # Note: TikTok's API has specific requirements and approval process
        
        return {
            'success': False,
            'error': 'TikTok integration coming soon - requires video content and API approval'
        }
    
    def _post_to_linkedin(self, account: SocialAccount, post: SocialPost) -> Dict[str, Any]:
        """Post to LinkedIn"""
        
        url = "https://api.linkedin.com/v2/ugcPosts"
        
        headers = {
            'Authorization': f'Bearer {account.access_token}',
            'Content-Type': 'application/json',
            'X-Restli-Protocol-Version': '2.0.0'
        }
        
        data = {
            'author': f'urn:li:person:{account.platform_user_id}',
            'lifecycleState': 'PUBLISHED',
            'specificContent': {
                'com.linkedin.ugc.ShareContent': {
                    'shareCommentary': {
                        'text': post.content
                    },
                    'shareMediaCategory': 'NONE'
                }
            },
            'visibility': {
                'com.linkedin.ugc.MemberNetworkVisibility': 'PUBLIC'
            }
        }
        
        # Add media if available
        if post.image_url:
            data['specificContent']['com.linkedin.ugc.ShareContent']['shareMediaCategory'] = 'IMAGE'
            # Would need to upload media first and get media URN
        
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 201:
            result = response.json()
            return {
                'success': True,
                'post_id': result.get('id'),
                'platform_response': result
            }
        else:
            return {
                'success': False,
                'error': f"LinkedIn API error: {response.text}"
            }
    
    def _refresh_token(self, account: SocialAccount) -> Dict[str, Any]:
        """Refresh access token for account"""
        
        if not account.refresh_token:
            return {
                'success': False,
                'error': 'No refresh token available'
            }
        
        platform_config = self.platform_configs.get(account.platform)
        if not platform_config:
            return {
                'success': False,
                'error': f'Platform {account.platform} not configured'
            }
        
        # Platform-specific token refresh logic would go here
        # This is a simplified placeholder
        
        return {
            'success': False,
            'error': 'Token refresh not implemented for this platform'
        }
    
    def _get_platform_configs(self) -> Dict[str, Dict[str, str]]:
        """Get platform-specific configuration"""
        return {
            'facebook': {
                'auth_url': 'https://www.facebook.com/v18.0/dialog/oauth',
                'token_url': 'https://graph.facebook.com/v18.0/oauth/access_token',
                'api_base': 'https://graph.facebook.com'
            },
            'instagram': {
                'auth_url': 'https://api.instagram.com/oauth/authorize',
                'token_url': 'https://api.instagram.com/oauth/access_token',
                'api_base': 'https://graph.facebook.com'
            },
            'twitter': {
                'auth_url': 'https://twitter.com/i/oauth2/authorize',
                'token_url': 'https://api.twitter.com/2/oauth2/token',
                'api_base': 'https://api.twitter.com'
            },
            'tiktok': {
                'auth_url': 'https://www.tiktok.com/auth/authorize/',
                'token_url': 'https://open-api.tiktok.com/oauth/access_token/',
                'api_base': 'https://open-api.tiktok.com'
            },
            'linkedin': {
                'auth_url': 'https://www.linkedin.com/oauth/v2/authorization',
                'token_url': 'https://www.linkedin.com/oauth/v2/accessToken',
                'api_base': 'https://api.linkedin.com'
            }
        }
    
    def get_platform_auth_url(self, platform: str, redirect_uri: str) -> str:
        """Get OAuth URL for platform authentication"""
        
        config = self.platform_configs.get(platform)
        if not config:
            raise ValueError(f"Platform {platform} not supported")
        
        # Platform-specific OAuth URL generation would go here
        # This is a simplified placeholder
        
        return f"{config['auth_url']}?redirect_uri={redirect_uri}&platform={platform}"
    
    def process_scheduled_posts(self) -> Dict[str, Any]:
        """Process scheduled posts that are ready to be posted"""
        
        from models import db
        
        # Get posts scheduled for now or earlier
        ready_posts = SocialPost.query.filter(
            SocialPost.status == 'scheduled',
            SocialPost.scheduled_for <= datetime.utcnow()
        ).all()
        
        results = {
            'processed': 0,
            'successful': 0,
            'failed': 0,
            'errors': []
        }
        
        for post in ready_posts:
            results['processed'] += 1
            
            try:
                result = self.post_to_platform(post)
                
                if result['success']:
                    results['successful'] += 1
                    
                    # Handle recurring posts
                    if post.is_recurring and post.post_frequency != 'once':
                        self._schedule_next_recurring_post(post)
                else:
                    results['failed'] += 1
                    results['errors'].append(f"Post {post.id}: {result.get('error')}")
                    
            except Exception as e:
                results['failed'] += 1
                results['errors'].append(f"Post {post.id}: {str(e)}")
        
        return results
    
    def _schedule_next_recurring_post(self, post: SocialPost):
        """Schedule the next instance of a recurring post"""
        
        from models import db
        
        # Calculate next post time based on frequency
        if post.post_frequency == 'daily':
            next_time = post.scheduled_for + timedelta(days=1)
        elif post.post_frequency == 'weekly':
            next_time = post.scheduled_for + timedelta(weeks=1)
        elif post.post_frequency == 'monthly':
            next_time = post.scheduled_for + timedelta(days=30)
        else:
            return
        
        # Create new scheduled post
        new_post = SocialPost()
        new_post.user_id = post.user_id
        new_post.campaign_id = post.campaign_id
        new_post.platform = post.platform
        new_post.content = post.content
        new_post.scheduled_for = next_time
        new_post.post_frequency = post.post_frequency
        new_post.is_recurring = True
        new_post.status = 'scheduled'
        
        db.session.add(new_post)
        db.session.commit()