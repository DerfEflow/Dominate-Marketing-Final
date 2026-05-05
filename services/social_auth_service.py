"""
Social Media Authentication Service
Handles OAuth flows for connecting social media accounts
"""

import logging
import requests
import os
from typing import Dict, Any, Optional
from models import SocialAccount, User
from models import db
from urllib.parse import urlencode

logger = logging.getLogger(__name__)

class SocialAuthService:
    """Service for handling social media OAuth authentication"""
    
    def __init__(self):
        self.platform_configs = {
            'facebook': {
                'client_id': os.getenv('FACEBOOK_CLIENT_ID'),
                'client_secret': os.getenv('FACEBOOK_CLIENT_SECRET'),
                'auth_url': 'https://www.facebook.com/v18.0/dialog/oauth',
                'token_url': 'https://graph.facebook.com/v18.0/oauth/access_token',
                'scope': 'pages_manage_posts,pages_read_engagement,instagram_basic,instagram_content_publish'
            },
            'instagram': {
                'client_id': os.getenv('FACEBOOK_CLIENT_ID'),  # Instagram uses Facebook OAuth
                'client_secret': os.getenv('FACEBOOK_CLIENT_SECRET'),
                'auth_url': 'https://www.facebook.com/v18.0/dialog/oauth',
                'token_url': 'https://graph.facebook.com/v18.0/oauth/access_token',
                'scope': 'instagram_basic,instagram_content_publish'
            },
            'twitter': {
                'client_id': os.getenv('TWITTER_CLIENT_ID'),
                'client_secret': os.getenv('TWITTER_CLIENT_SECRET'),
                'auth_url': 'https://twitter.com/i/oauth2/authorize',
                'token_url': 'https://api.twitter.com/2/oauth2/token',
                'scope': 'tweet.read,tweet.write,users.read'
            },
            'linkedin': {
                'client_id': os.getenv('LINKEDIN_CLIENT_ID'),
                'client_secret': os.getenv('LINKEDIN_CLIENT_SECRET'),
                'auth_url': 'https://www.linkedin.com/oauth/v2/authorization',
                'token_url': 'https://www.linkedin.com/oauth/v2/accessToken',
                'scope': 'r_liteprofile,r_emailaddress,w_member_social'
            },
            'tiktok': {
                'client_id': os.getenv('TIKTOK_CLIENT_ID'),
                'client_secret': os.getenv('TIKTOK_CLIENT_SECRET'),
                'auth_url': 'https://www.tiktok.com/auth/authorize/',
                'token_url': 'https://open-api.tiktok.com/oauth/access_token/',
                'scope': 'user.info.basic,video.upload'
            }
        }
    
    def get_auth_url(self, platform: str, user_id: str, redirect_uri: str) -> Optional[str]:
        """Generate OAuth authorization URL for platform"""
        
        config = self.platform_configs.get(platform)
        if not config or not config['client_id']:
            return None
        
        params = {
            'client_id': config['client_id'],
            'redirect_uri': redirect_uri,
            'scope': config['scope'],
            'response_type': 'code',
            'state': f"{user_id}:{platform}"  # Include user and platform in state
        }
        
        return f"{config['auth_url']}?{urlencode(params)}"
    
    def handle_oauth_callback(self, platform: str, code: str, state: str, redirect_uri: str) -> Dict[str, Any]:
        """Handle OAuth callback and exchange code for access token"""
        
        try:
            # Parse state to get user_id and platform
            user_id, platform_from_state = state.split(':')
            
            if platform != platform_from_state:
                return {
                    'success': False,
                    'error': 'State parameter mismatch'
                }
            
            config = self.platform_configs.get(platform)
            if not config:
                return {
                    'success': False,
                    'error': f'Platform {platform} not configured'
                }
            
            # Exchange code for access token
            token_data = {
                'client_id': config['client_id'],
                'client_secret': config['client_secret'],
                'code': code,
                'redirect_uri': redirect_uri,
                'grant_type': 'authorization_code'
            }
            
            response = requests.post(config['token_url'], data=token_data)
            
            if response.status_code != 200:
                return {
                    'success': False,
                    'error': f'Token exchange failed: {response.text}'
                }
            
            token_info = response.json()
            access_token = token_info.get('access_token')
            
            if not access_token:
                return {
                    'success': False,
                    'error': 'No access token received'
                }
            
            # Get user profile information
            profile_info = self._get_user_profile(platform, access_token)
            
            if not profile_info['success']:
                return {
                    'success': False,
                    'error': f'Failed to get user profile: {profile_info.get("error")}'
                }
            
            # Save or update social account
            account = self._save_social_account(
                user_id=user_id,
                platform=platform,
                access_token=access_token,
                refresh_token=token_info.get('refresh_token'),
                expires_in=token_info.get('expires_in'),
                profile_info=profile_info['data']
            )
            
            return {
                'success': True,
                'account': account,
                'profile': profile_info['data']
            }
            
        except Exception as e:
            logger.error(f"OAuth callback error for {platform}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_user_profile(self, platform: str, access_token: str) -> Dict[str, Any]:
        """Get user profile information from platform"""
        
        try:
            if platform == 'facebook':
                url = 'https://graph.facebook.com/me?fields=id,name,email'
                headers = {'Authorization': f'Bearer {access_token}'}
                
            elif platform == 'instagram':
                url = 'https://graph.instagram.com/me?fields=id,username'
                headers = {'Authorization': f'Bearer {access_token}'}
                
            elif platform == 'twitter':
                url = 'https://api.twitter.com/2/users/me'
                headers = {'Authorization': f'Bearer {access_token}'}
                
            elif platform == 'linkedin':
                url = 'https://api.linkedin.com/v2/people/~'
                headers = {'Authorization': f'Bearer {access_token}'}
                
            elif platform == 'tiktok':
                url = 'https://open-api.tiktok.com/oauth/userinfo/'
                headers = {'Authorization': f'Bearer {access_token}'}
                
            else:
                return {
                    'success': False,
                    'error': f'Profile fetch not implemented for {platform}'
                }
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                profile_data = response.json()
                return {
                    'success': True,
                    'data': profile_data
                }
            else:
                return {
                    'success': False,
                    'error': f'Profile API error: {response.text}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _save_social_account(self, user_id: str, platform: str, access_token: str,
                           refresh_token: str, expires_in: int, profile_info: Dict[str, Any]) -> SocialAccount:
        """Save or update social media account"""
        
        from datetime import datetime, timedelta
        
        # Check if account already exists
        existing = SocialAccount.query.filter_by(
            user_id=user_id,
            platform=platform,
            platform_user_id=str(profile_info.get('id'))
        ).first()
        
        if existing:
            # Update existing account
            existing.access_token = access_token
            existing.refresh_token = refresh_token
            existing.username = profile_info.get('name') or profile_info.get('username')
            existing.is_active = True
            
            if expires_in:
                existing.token_expires = datetime.utcnow() + timedelta(seconds=expires_in)
            
            db.session.commit()
            return existing
        
        else:
            # Create new account
            account = SocialAccount()
            account.user_id = user_id
            account.platform = platform
            account.platform_user_id = str(profile_info.get('id'))
            account.username = profile_info.get('name') or profile_info.get('username')
            account.access_token = access_token
            account.refresh_token = refresh_token
            account.is_active = True
            
            if expires_in:
                account.token_expires = datetime.utcnow() + timedelta(seconds=expires_in)
            
            db.session.add(account)
            db.session.commit()
            return account
    
    def refresh_access_token(self, account: SocialAccount) -> Dict[str, Any]:
        """Refresh expired access token"""
        
        if not account.refresh_token:
            return {
                'success': False,
                'error': 'No refresh token available'
            }
        
        config = self.platform_configs.get(account.platform)
        if not config:
            return {
                'success': False,
                'error': f'Platform {account.platform} not configured'
            }
        
        try:
            data = {
                'client_id': config['client_id'],
                'client_secret': config['client_secret'],
                'refresh_token': account.refresh_token,
                'grant_type': 'refresh_token'
            }
            
            response = requests.post(config['token_url'], data=data)
            
            if response.status_code == 200:
                token_info = response.json()
                
                # Update account with new token
                account.access_token = token_info.get('access_token')
                if token_info.get('refresh_token'):
                    account.refresh_token = token_info.get('refresh_token')
                
                if token_info.get('expires_in'):
                    from datetime import datetime, timedelta
                    account.token_expires = datetime.utcnow() + timedelta(seconds=token_info['expires_in'])
                
                db.session.commit()
                
                return {
                    'success': True,
                    'access_token': account.access_token
                }
            else:
                return {
                    'success': False,
                    'error': f'Token refresh failed: {response.text}'
                }
                
        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def disconnect_account(self, user_id: str, platform: str) -> Dict[str, Any]:
        """Disconnect social media account"""
        
        try:
            account = SocialAccount.query.filter_by(
                user_id=user_id,
                platform=platform,
                is_active=True
            ).first()
            
            if account:
                account.is_active = False
                db.session.commit()
                
                return {
                    'success': True,
                    'message': f'{platform.title()} account disconnected'
                }
            else:
                return {
                    'success': False,
                    'error': f'No active {platform} account found'
                }
                
        except Exception as e:
            logger.error(f"Disconnect error: {e}")
            return {
                'success': False,
                'error': str(e)
            }

# Global auth service instance
social_auth_service = SocialAuthService()