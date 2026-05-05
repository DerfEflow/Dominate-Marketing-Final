"""
User-specific campaign generation service.
Every user gets completely fresh analysis and content generation.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, Any

from services.sell_profile_analyzer import SellProfileAnalyzer
from services.viral_tools_researcher import ViralToolsResearcher
from services.content_generator import ContentGenerator
from services.quality_agent import QualityAgent

logger = logging.getLogger(__name__)

class UserCampaignGenerator:
    """Generates completely fresh campaigns for each user based on their input"""
    
    def __init__(self):
        # Initialize all services fresh for each user
        self.profile_analyzer = SellProfileAnalyzer()
        self.viral_researcher = ViralToolsResearcher()
        self.content_generator = ContentGenerator()
        self.quality_agent = QualityAgent()
    
    def generate_fresh_campaign(self, user_input: Dict[str, Any], user_tier: str, user_id: str) -> Dict[str, Any]:
        """
        Generate completely fresh campaign using user's specific input.
        No static data or cached content - everything starts from scratch.
        """
        try:
            campaign_id = str(uuid.uuid4())
            logger.info(f"Starting fresh campaign generation {campaign_id} for user {user_id}")
            
            # Extract user inputs
            business_url = user_input['business_url']
            target_audience = user_input.get('target_audience', '')
            campaign_goal = user_input.get('campaign_goal', 'leads')
            brand_voice = user_input.get('brand_voice', 'professional')
            title = user_input.get('title', '')
            
            # Step 1: Fresh Sell Profile Analysis (user's business only)
            logger.info(f"Analyzing {business_url} fresh for user {user_id}")
            user_sell_profile = self.profile_analyzer.analyze_website(business_url)
            profile_data = self.profile_analyzer.export_profile(user_sell_profile)
            
            # Step 2: Fresh Viral Tools Research (based on user's business)
            logger.info(f"Researching viral tools for {profile_data.get('business_name', 'business')}")
            user_viral_tools = self.viral_researcher.research_viral_tools(profile_data)
            viral_data = self.viral_researcher.export_research(user_viral_tools)
            
            # Step 3: Generate Fresh AI Content (unique to this user)
            logger.info(f"Generating fresh AI content for user {user_id} at {user_tier} tier")
            user_generated_content = self.content_generator.generate_campaign_content(
                profile_data, viral_data, tier=user_tier
            )
            
            # Step 4: Fresh Quality Validation (specific to this user's content)
            logger.info(f"Quality validation for user {user_id} campaign")
            user_quality_validation = self.quality_agent.validate_campaign_content(
                user_generated_content, profile_data
            )
            
            # Step 5: Compile Fresh Campaign Results
            fresh_campaign = {
                'campaign_id': campaign_id,
                'user_id': user_id,
                'generated_at': datetime.now().isoformat(),
                'success': True,
                'status': 'completed',
                
                # User's fresh business intelligence
                'sell_profile': profile_data,
                
                # Fresh viral research for this user
                'viral_tools': viral_data,
                
                # Freshly generated content
                'generated_content': user_generated_content,
                
                # Fresh quality validation
                'quality_validation': user_quality_validation,
                
                # User's original inputs
                'user_inputs': {
                    'business_url': business_url,
                    'target_audience': target_audience,
                    'campaign_goal': campaign_goal,
                    'brand_voice': brand_voice,
                    'title': title
                },
                
                # Metadata
                'generation_metadata': {
                    'tier_used': user_tier,
                    'services_used': ['SellProfileAnalyzer', 'ViralToolsResearcher', 'ContentGenerator', 'QualityAgent'],
                    'ai_models_used': self._get_tier_models(user_tier),
                    'total_content_pieces': self._count_content_pieces(user_generated_content),
                    'confidence_scores': {
                        'sell_profile': user_sell_profile.confidence_score,
                        'viral_tools': viral_data.get('confidence_score', 0.85),
                        'quality_validation': user_quality_validation.get('overall_score', 85) / 100
                    }
                }
            }
            
            logger.info(f"Fresh campaign {campaign_id} completed successfully for user {user_id}")
            return fresh_campaign
            
        except Exception as e:
            logger.error(f"Error generating fresh campaign for user {user_id}: {e}")
            return {
                'success': False,
                'campaign_id': str(uuid.uuid4()),
                'user_id': user_id,
                'error': str(e),
                'generated_at': datetime.now().isoformat()
            }
    
    def _get_tier_models(self, tier: str) -> list:
        """Get AI models used based on user tier"""
        tier_models = {
            'basic': ['GPT-4o-mini', 'Claude Sonnet 4'],
            'plus': ['GPT-4o-mini', 'DALL-E 3', 'Claude Sonnet 4'],
            'pro': ['GPT-4o', 'DALL-E 3', 'Google VEO 3', 'Claude Sonnet 4'],
            'enterprise': ['GPT-4o', 'DALL-E 3', 'Google VEO 3', 'Pika Labs', 'Claude Sonnet 4']
        }
        return tier_models.get(tier or 'basic', ['GPT-4o-mini', 'Claude Sonnet 4'])
    
    def _count_content_pieces(self, generated_content: Dict) -> int:
        """Count total content pieces generated"""
        count = 0
        count += len(generated_content.get('text_content', []))
        count += len(generated_content.get('image_content', []))
        count += len(generated_content.get('video_content', []))
        count += len(generated_content.get('combined_content', []))
        return count
    
    def regenerate_specific_content(self, campaign_data: Dict, content_type: str, user_feedback: str = None) -> Dict[str, Any]:
        """
        Regenerate specific content type based on user feedback.
        This allows users to request fresh content without regenerating everything.
        """
        try:
            logger.info(f"Regenerating {content_type} for campaign {campaign_data.get('campaign_id')}")
            
            # Extract existing data
            profile_data = campaign_data.get('sell_profile', {})
            viral_data = campaign_data.get('viral_tools', {})
            tier = campaign_data.get('generation_metadata', {}).get('tier_used', 'basic')
            
            # Generate fresh content of specific type using existing methods
            if content_type == 'text':
                new_content = self.content_generator.generate_campaign_content(profile_data, viral_data, tier)
                new_content = new_content.get('text_content', [])
            elif content_type == 'image':
                new_content = self.content_generator.generate_campaign_content(profile_data, viral_data, tier)
                new_content = new_content.get('image_content', [])
            elif content_type == 'video':
                new_content = self.content_generator.generate_campaign_content(profile_data, viral_data, tier)
                new_content = new_content.get('video_content', [])
            else:
                raise ValueError(f"Unknown content type: {content_type}")
            
            # Quality validation for new content using existing method
            quality_check = self.quality_agent.validate_campaign_content({'generated_content': new_content}, profile_data)
            
            return {
                'success': True,
                'content_type': content_type,
                'new_content': new_content,
                'quality_validation': quality_check,
                'regenerated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error regenerating {content_type}: {e}")
            return {
                'success': False,
                'error': str(e),
                'content_type': content_type
            }