"""
Social Media Scheduler Service
Background service for processing scheduled posts and managing social media automation
"""

import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List
from models import SocialPost, SocialAccount, Campaign
from models import db
from services.social_media_integration import SocialMediaService

logger = logging.getLogger(__name__)

class SocialScheduler:
    """Background scheduler for social media posts"""
    
    def __init__(self):
        self.social_service = SocialMediaService()
        self.running = False
        self.scheduler_thread = None
        self.check_interval = 60  # Check every minute
    
    def start_scheduler(self):
        """Start the background scheduler"""
        if self.running:
            return
        
        self.running = True
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        logger.info("Social media scheduler started")
    
    def stop_scheduler(self):
        """Stop the background scheduler"""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        logger.info("Social media scheduler stopped")
    
    def _run_scheduler(self):
        """Main scheduler loop"""
        while self.running:
            try:
                self._process_scheduled_posts()
                self._cleanup_old_posts()
                self.process_research_refresh()

                # Sleep for check interval
                time.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                time.sleep(60)  # Wait longer on error
    
    def process_due_posts(self):
        """Public entry point used by the worker process and manual triggers.

        Publishes any posts whose scheduled time has arrived, then cleans up old
        ones. (The worker __main__ and the admin "run now" action call this.)
        """
        self._process_scheduled_posts()
        self._cleanup_old_posts()

    def process_research_refresh(self):
        """Re-run the automation cycle for clients whose source data is stale.

        This is the 'continual fresh source data' driver: automation-enabled
        clients get their research refreshed + new posts generated and scheduled
        on their cadence.
        """
        try:
            from services.automation_engine import run_due_clients
            ran = run_due_clients()
            if ran:
                logger.info(f"Automation: refreshed {len(ran)} client(s)")
            return ran
        except Exception as e:
            logger.error(f"Automation refresh error: {e}")
            return []

    def _process_scheduled_posts(self):
        """Process posts scheduled for now or earlier"""
        
        try:
            # Get posts ready to be posted
            ready_posts = SocialPost.query.filter(
                SocialPost.status == 'scheduled',
                SocialPost.scheduled_for <= datetime.utcnow()
            ).all()
            
            if not ready_posts:
                return
            
            logger.info(f"Processing {len(ready_posts)} scheduled posts")
            
            for post in ready_posts:
                try:
                    # Check the post's CLIENT (brand) has this platform connected,
                    # falling back to the user's account. (Matches the resolution
                    # in SocialMediaService.post_to_platform.)
                    brand_id = None
                    if post.campaign_id:
                        camp = Campaign.query.get(post.campaign_id)
                        brand_id = camp.brand_id if camp else None
                    account = None
                    if brand_id:
                        account = SocialAccount.query.filter_by(
                            brand_id=brand_id, platform=post.platform, is_active=True
                        ).first()
                    if not account:
                        account = SocialAccount.query.filter_by(
                            user_id=post.user_id, platform=post.platform, is_active=True
                        ).first()

                    if not account:
                        post.status = 'failed'
                        post.error_message = f'No connected {post.platform} account'
                        db.session.commit()
                        continue
                    
                    # Post to platform
                    result = self.social_service.post_to_platform(post)
                    
                    if result['success']:
                        logger.info(f"Successfully posted to {post.platform} for user {post.user_id}")
                        
                        # Schedule next recurring post if applicable
                        if post.is_recurring and post.post_frequency != 'once':
                            self._schedule_next_recurring_post(post)
                    else:
                        logger.error(f"Failed to post to {post.platform}: {result.get('error')}")
                
                except Exception as e:
                    logger.error(f"Error processing post {post.id}: {e}")
                    post.status = 'failed'
                    post.error_message = str(e)
                    db.session.commit()
            
        except Exception as e:
            logger.error(f"Error processing scheduled posts: {e}")
    
    def _schedule_next_recurring_post(self, post: SocialPost):
        """Schedule the next instance of a recurring post"""
        
        try:
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
            new_post.image_url = post.image_url
            new_post.video_url = post.video_url
            
            db.session.add(new_post)
            db.session.commit()
            
            logger.info(f"Scheduled next recurring post for {post.platform} at {next_time}")
            
        except Exception as e:
            logger.error(f"Error scheduling next recurring post: {e}")
    
    def _cleanup_old_posts(self):
        """Clean up old completed posts to prevent database bloat"""
        
        try:
            # Delete posted posts older than 30 days
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            
            old_posts = SocialPost.query.filter(
                SocialPost.status == 'posted',
                SocialPost.posted_at < cutoff_date
            ).limit(100)  # Process in batches
            
            count = old_posts.count()
            if count > 0:
                for post in old_posts:
                    db.session.delete(post)
                
                db.session.commit()
                logger.info(f"Cleaned up {count} old posts")
                
        except Exception as e:
            logger.error(f"Error cleaning up old posts: {e}")
    
    def get_scheduler_status(self) -> Dict[str, Any]:
        """Get scheduler status and statistics"""
        
        try:
            stats = {
                'running': self.running,
                'check_interval': self.check_interval,
                'scheduled_posts': SocialPost.query.filter_by(status='scheduled').count(),
                'pending_posts': SocialPost.query.filter(
                    SocialPost.status == 'scheduled',
                    SocialPost.scheduled_for <= datetime.utcnow() + timedelta(hours=1)
                ).count(),
                'recent_posts': SocialPost.query.filter(
                    SocialPost.posted_at >= datetime.utcnow() - timedelta(hours=24)
                ).count(),
                'last_check': datetime.utcnow().isoformat()
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting scheduler status: {e}")
            return {'error': str(e)}
    
    def schedule_immediate_post(self, user_id: str, campaign_id: str, platforms: List[str], 
                              content: str, media_urls: Dict[str, str] = None) -> Dict[str, Any]:
        """Schedule a post to go out immediately"""
        
        try:
            results = []
            
            for platform in platforms:
                post = SocialPost()
                post.user_id = user_id
                post.campaign_id = campaign_id
                post.platform = platform
                post.content = content
                post.scheduled_for = datetime.utcnow()
                post.status = 'scheduled'
                
                if media_urls:
                    post.image_url = media_urls.get('image')
                    post.video_url = media_urls.get('video')
                
                db.session.add(post)
                db.session.commit()
                
                # Post immediately
                result = self.social_service.post_to_platform(post)
                results.append({
                    'platform': platform,
                    'success': result['success'],
                    'error': result.get('error')
                })
            
            return {
                'success': True,
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Error scheduling immediate post: {e}")
            return {
                'success': False,
                'error': str(e)
            }

# Global scheduler instance
social_scheduler = SocialScheduler()

if __name__ == '__main__':
    """
    Standalone worker entry point for Railway's worker process.
    Run with: python services/social_scheduler.py
    """
    import os, sys, time, logging
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    
    from main_app import create_app
    flask_app = create_app()
    
    with flask_app.app_context():
        scheduler = SocialScheduler()
        logging.info("Social scheduler worker started")
        while True:
            try:
                scheduler.process_due_posts()
                scheduler.process_research_refresh()
            except Exception as e:
                logging.error(f"Scheduler error: {e}")
            time.sleep(60)
