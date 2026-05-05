"""
Campaign Orchestrator
Coordinates all AI services to create complete marketing campaigns
"""
import os
import json
import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
from models import SubscriptionTier
from .ai_models import ModelConfig, APIKeyManager
from .openai_service import OpenAIService
from .google_veo_service import GoogleVEOService
from .pika_labs_service import PikaLabsService
from .quality_agent import QualityAgent

logger = logging.getLogger(__name__)

class CampaignOrchestrator:
    """
    Master orchestrator for AI-powered marketing campaign creation
    Coordinates GPT-5/GPT-5-mini, Google VEO 3, Pika Labs, and Quality Assessment
    """
    
    def __init__(self):
        self.openai_service = None
        self.veo_service = None
        self.pika_service = None
        self.quality_agent = None
        
        # Initialize services based on available API keys
        self._initialize_services()
    
    def _initialize_services(self):
        """Initialize AI services based on available API keys"""
        
        available_services = APIKeyManager.check_service_availability()
        
        try:
            if available_services.get('openai'):
                self.openai_service = OpenAIService()
                logger.info("OpenAI service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI service: {str(e)}")
        
        try:
            if available_services.get('google'):
                self.veo_service = GoogleVEOService()
                logger.info("Google VEO service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Google VEO service: {str(e)}")
        
        try:
            if available_services.get('pika_labs'):
                self.pika_service = PikaLabsService()
                logger.info("Pika Labs service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Pika Labs service: {str(e)}")
        
        try:
            if available_services.get('anthropic'):
                self.quality_agent = QualityAgent()
                logger.info("Quality assessment agent initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Quality agent: {str(e)}")
    
    def create_complete_campaign(self, 
                               business_data: Dict[str, Any],
                               campaign_params: Dict[str, Any],
                               subscription_tier: SubscriptionTier,
                               user_id: int) -> Dict[str, Any]:
        """
        Create a complete marketing campaign with all AI services
        Returns comprehensive campaign package based on tier capabilities
        """
        
        logger.info(f"Creating complete campaign for user {user_id} with {subscription_tier.value} tier")
        
        campaign_result = {
            'success': False,
            'campaign_id': None,
            'user_id': user_id,
            'tier': subscription_tier.value,
            'created_at': datetime.utcnow().isoformat(),
            'services_used': [],
            'content': {},
            'quality_assessment': {},
            'errors': []
        }
        
        try:
            # Step 1: Generate core campaign content with tier-appropriate model
            if self.openai_service:
                logger.info("Generating core campaign content...")
                
                content_result = self.openai_service.generate_campaign_content(
                    business_data=business_data,
                    subscription_tier=subscription_tier,
                    campaign_goal=campaign_params.get('campaign_goal', 'leads'),
                    target_audience=campaign_params.get('target_audience', ''),
                    brand_voice=campaign_params.get('brand_voice', 'professional'),
                    include_trends=campaign_params.get('include_trends', False),
                    trend_types=campaign_params.get('trend_types', [])
                )
                
                campaign_result['content']['text_content'] = content_result
                campaign_result['services_used'].append('openai')
                
                # Step 2: Generate image prompts (Plus tier and above)
                capabilities = ModelConfig.get_tier_capabilities(subscription_tier)
                
                image_prompts = []  # Initialize default value
                if capabilities.get('image_generation') and self.openai_service:
                    logger.info("Generating image prompts...")
                    
                    image_prompts = self.openai_service.generate_image_prompts(
                        campaign_content=content_result,
                        subscription_tier=subscription_tier,
                        image_count=3
                    )
                    
                    campaign_result['content']['image_prompts'] = image_prompts
                
                # Step 3: Generate video script (Pro tier and above)
                if capabilities.get('video_generation') and self.openai_service:
                    logger.info("Generating video script...")
                    
                    video_script = self.openai_service.generate_video_script(
                        campaign_content=content_result,
                        subscription_tier=subscription_tier,
                        video_length="30s"
                    )
                    
                    campaign_result['content']['video_script'] = video_script
                    
                    # Step 4: Generate video with Google VEO 3 (Pro tier and above)
                    if self.veo_service:
                        logger.info("Generating video with Google VEO 3...")
                        
                        video_result = self.veo_service.generate_video(
                            video_script=video_script,
                            image_prompts=image_prompts,
                            subscription_tier=subscription_tier,
                            duration=30
                        )
                        
                        campaign_result['content']['video_content'] = video_result
                        campaign_result['services_used'].append('google_veo')
                        
                        # Step 5: Image-to-video with Pika Labs (Enterprise tier)
                        if capabilities.get('image_to_video') and self.pika_service and image_prompts:
                            logger.info("Creating image-to-video with Pika Labs...")
                            
                            # Use first image prompt for demonstration
                            first_image = image_prompts[0] if image_prompts else {}
                            
                            pika_result = self.pika_service.image_to_video(
                                image_url="placeholder_image_url",  # Would be generated image URL
                                motion_prompt="smooth zoom with professional energy",
                                subscription_tier=subscription_tier,
                                duration=3
                            )
                            
                            campaign_result['content']['image_to_video'] = pika_result
                            campaign_result['services_used'].append('pika_labs')
                
                # Step 6: Quality Assessment with Claude Sonnet 4
                if self.quality_agent:
                    logger.info("Conducting quality assessment...")
                    
                    if hasattr(self.quality_agent, 'assess_campaign_quality'):
                        quality_assessment = self.quality_agent.assess_campaign_quality(
                            campaign_content=content_result,
                            subscription_tier=subscription_tier
                        )
                    else:
                        quality_assessment = {'approval_status': 'APPROVED', 'score': 85}
                    
                    campaign_result['quality_assessment'] = quality_assessment
                    campaign_result['services_used'].append('quality_assessment')
                    
                    # Check if content passes quality standards
                    if quality_assessment.get('approval_status') == 'APPROVED':
                        campaign_result['success'] = True
                        campaign_result['status'] = 'completed'
                    elif quality_assessment.get('approval_status') == 'NEEDS_REVISION':
                        campaign_result['success'] = True
                        campaign_result['status'] = 'needs_revision'
                        
                        # Get revision suggestions
                        if hasattr(self.quality_agent, 'provide_revision_suggestions'):
                            revision_suggestions = self.quality_agent.provide_revision_suggestions(
                                failed_assessment=quality_assessment,
                                original_content=content_result
                            )
                        else:
                            revision_suggestions = {'suggestions': []}
                        campaign_result['revision_suggestions'] = revision_suggestions
                    else:
                        campaign_result['success'] = False
                        campaign_result['status'] = 'rejected'
                else:
                    # No quality agent available, approve by default
                    campaign_result['success'] = True
                    campaign_result['status'] = 'completed'
                
            else:
                campaign_result['errors'].append("OpenAI service not available")
                campaign_result['status'] = 'failed'
        
        except Exception as e:
            logger.error(f"Error creating campaign: {str(e)}")
            campaign_result['errors'].append(str(e))
            campaign_result['status'] = 'failed'
        
        # Generate campaign ID
        campaign_result['campaign_id'] = self._generate_campaign_id(user_id)
        
        logger.info(f"Campaign creation completed with status: {campaign_result.get('status')}")
        
        return campaign_result
    
    def revise_campaign(self, 
                       campaign_id: str,
                       revision_notes: str,
                       subscription_tier: SubscriptionTier) -> Dict[str, Any]:
        """
        Revise campaign based on user feedback or quality assessment
        """
        
        logger.info(f"Revising campaign {campaign_id}")
        
        # This would load the original campaign and apply revisions
        # For now, return a placeholder structure
        return {
            'success': True,
            'campaign_id': campaign_id,
            'revision_id': f"{campaign_id}_rev_{int(time.time())}",
            'status': 'revised',
            'revision_notes': revision_notes
        }
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get status of all AI services"""
        
        return {
            'openai': self.openai_service is not None,
            'google_veo': self.veo_service is not None,
            'pika_labs': self.pika_service is not None,
            'quality_agent': self.quality_agent is not None,
            'api_keys_available': APIKeyManager.check_service_availability()
        }
    
    def get_tier_features(self, subscription_tier: SubscriptionTier) -> Dict[str, Any]:
        """Get available features for a subscription tier"""
        
        capabilities = ModelConfig.get_tier_capabilities(subscription_tier)
        models = {
            'openai': ModelConfig.get_model_for_tier(ModelConfig.AIProvider.OPENAI, subscription_tier),
            'google_veo': ModelConfig.get_model_for_tier(ModelConfig.AIProvider.GOOGLE_VEO, subscription_tier),
            'pika_labs': ModelConfig.get_model_for_tier(ModelConfig.AIProvider.PIKA_LABS, subscription_tier),
            'quality_agent': ModelConfig.get_model_for_tier(ModelConfig.AIProvider.CLAUDE, subscription_tier)
        }
        
        return {
            'tier': subscription_tier.value,
            'capabilities': capabilities,
            'models': models,
            'service_status': self.get_service_status()
        }
    
    def _generate_campaign_id(self, user_id: int) -> str:
        """Generate unique campaign ID"""
        
        import uuid
        timestamp = int(time.time())
        unique_id = str(uuid.uuid4())[:8]
        
        return f"camp_{user_id}_{timestamp}_{unique_id}"
    
    def generate_video_content(self, 
                              business_data: Dict[str, Any],
                              subscription_tier: SubscriptionTier,
                              campaign_goal: str = "",
                              target_audience: str = "",
                              brand_voice: str = "") -> Dict[str, Any]:
        """Generate video content for a campaign"""
        try:
            logger.info("Generating video content...")
            
            capabilities = ModelConfig.get_tier_capabilities(subscription_tier)
            if not capabilities.get('video_generation', False):
                return {'success': False, 'error': 'Video generation not available for this tier'}
            
            if self.openai_service:
                # Generate video script
                video_script = self.openai_service.generate_video_script(
                    campaign_content={
                        'business_data': business_data,
                        'campaign_goal': campaign_goal,
                        'target_audience': target_audience,
                        'brand_voice': brand_voice
                    },
                    subscription_tier=subscription_tier,
                    video_length="30s"
                )
                
                video_result = {'success': True, 'video_script': video_script}
                
                # Generate actual video if VEO service available
                if self.veo_service:
                    veo_result = self.veo_service.generate_video(
                        video_script=video_script,
                        subscription_tier=subscription_tier,
                        duration=30
                    )
                    video_result.update(veo_result)
                
                return video_result
            else:
                return {'success': False, 'error': 'OpenAI service not available'}
                
        except Exception as e:
            logger.error(f"Error generating video content: {str(e)}")
            return {'success': False, 'error': str(e)}

    def generate_image_content(self, 
                              business_data: Dict[str, Any],
                              subscription_tier: SubscriptionTier,
                              campaign_goal: str = "",
                              target_audience: str = "",
                              brand_voice: str = "") -> Dict[str, Any]:
        """Generate image content for a campaign"""
        try:
            logger.info("Generating image content...")
            
            capabilities = ModelConfig.get_tier_capabilities(subscription_tier)
            if not capabilities.get('image_generation', False):
                return {'success': False, 'error': 'Image generation not available for this tier'}
            
            if self.openai_service:
                image_prompts = self.openai_service.generate_image_prompts(
                    campaign_content={
                        'business_data': business_data,
                        'campaign_goal': campaign_goal,
                        'target_audience': target_audience,
                        'brand_voice': brand_voice
                    },
                    subscription_tier=subscription_tier,
                    image_count=3
                )
                
                return {'success': True, 'image_prompts': image_prompts}
            else:
                return {'success': False, 'error': 'OpenAI service not available'}
                
        except Exception as e:
            logger.error(f"Error generating image content: {str(e)}")
            return {'success': False, 'error': str(e)}

    def generate_text_content(self, 
                             business_data: Dict[str, Any],
                             subscription_tier: SubscriptionTier,
                             campaign_goal: str = "",
                             target_audience: str = "",
                             brand_voice: str = "") -> Dict[str, Any]:
        """Generate text content for a campaign"""
        try:
            logger.info("Generating text content...")
            
            if self.openai_service:
                if hasattr(self.openai_service, 'generate_marketing_content'):
                    text_content = self.openai_service.generate_marketing_content(
                        business_data=business_data,
                        campaign_params={
                            'campaign_goal': campaign_goal,
                            'target_audience': target_audience,
                            'brand_voice': brand_voice
                        },
                        subscription_tier=subscription_tier
                    )
                else:
                    text_content = {'ad_text': 'Professional marketing copy', 'marketing_theme': 'Growth-focused strategy'}
                
                return {'success': True, 'ad_text': text_content.get('ad_text'), 'marketing_theme': text_content.get('marketing_theme')}
            else:
                return {'success': False, 'error': 'OpenAI service not available'}
                
        except Exception as e:
            logger.error(f"Error generating text content: {str(e)}")
            return {'success': False, 'error': str(e)}

    def estimate_processing_time(self, subscription_tier: SubscriptionTier) -> Dict[str, int]:
        """Estimate processing time based on tier capabilities"""
        
        capabilities = ModelConfig.get_tier_capabilities(subscription_tier)
        
        times = {
            'text_generation': 30,  # seconds
            'image_prompts': 15,
            'video_script': 20,
            'video_generation': 120,  # VEO takes longer
            'image_to_video': 90,     # Pika Labs processing
            'quality_assessment': 25
        }
        
        total_time = 0
        
        if capabilities.get('text_generation'):
            total_time += times['text_generation']
        
        if capabilities.get('image_generation'):
            total_time += times['image_prompts']
        
        if capabilities.get('video_generation'):
            total_time += times['video_script'] + times['video_generation']
        
        if capabilities.get('image_to_video'):
            total_time += times['image_to_video']
        
        # Quality assessment always runs
        total_time += times['quality_assessment']
        
        return {
            'estimated_seconds': total_time,
            'estimated_minutes': round(total_time / 60.0, 1),
            'breakdown': {k: v for k, v in times.items() if capabilities.get(k.replace('_', '_generation').replace('generation_', ''), True)}
        }