"""
AI Model Configuration for Tier-Based Access
Handles model selection based on subscription tier
"""
import os
import logging
from enum import Enum
from typing import Dict, Any, Optional
from models import SubscriptionTier

# Configure logging
logger = logging.getLogger(__name__)

class AIProvider(Enum):
    OPENAI = "openai"
    GOOGLE_VEO = "google_veo"
    PIKA_LABS = "pika_labs"
    CLAUDE = "claude"  # For quality assessment

class ModelConfig:
    
    # Make AIProvider accessible as class attribute
    AIProvider = AIProvider
    """Configuration for AI models based on subscription tier"""
    
    # Premium tier models (Enterprise/Pro)
    PREMIUM_MODELS = {
        AIProvider.OPENAI: "gpt-4o",  # Most advanced for premium users
        AIProvider.GOOGLE_VEO: "veo-3",  # Video generation
        AIProvider.PIKA_LABS: "pika-1.5",  # Image to video manipulation
        AIProvider.CLAUDE: "claude-sonnet-4-5"  # Quality assessment
    }
    
    # Standard tier models (Basic/Plus) - Cost-optimized
    STANDARD_MODELS = {
        AIProvider.OPENAI: "gpt-4o-mini",  # Cost savings and speed
        AIProvider.GOOGLE_VEO: "veo-3",  # Same video generation
        AIProvider.PIKA_LABS: "pika-1.5",  # Same image manipulation
        AIProvider.CLAUDE: "claude-sonnet-4-5"  # Same quality assessment
    }
    
    @classmethod
    def get_model_for_tier(cls, provider: AIProvider, subscription_tier: SubscriptionTier) -> str:
        """Get appropriate model based on subscription tier"""
        
        # Premium tiers get advanced models
        if subscription_tier in [SubscriptionTier.PRO, SubscriptionTier.ENTERPRISE]:
            return cls.PREMIUM_MODELS.get(provider, "")
        
        # Standard tiers get cost-optimized models
        return cls.STANDARD_MODELS.get(provider, "")
    
    @classmethod
    def get_tier_capabilities(cls, subscription_tier: SubscriptionTier) -> Dict[str, bool]:
        """Get feature capabilities based on subscription tier"""
        
        capabilities = {
            "text_generation": True,
            "image_generation": False,
            "video_generation": False,
            "image_to_video": False,
            "quality_assessment": True,
            "advanced_prompts": False
        }
        
        if subscription_tier == SubscriptionTier.BASIC:
            return capabilities
        
        elif subscription_tier == SubscriptionTier.PLUS:
            capabilities.update({
                "image_generation": True,
            })
        
        elif subscription_tier == SubscriptionTier.PRO:
            capabilities.update({
                "image_generation": True,
                "video_generation": True,
                "advanced_prompts": True
            })
        
        elif subscription_tier == SubscriptionTier.ENTERPRISE:
            capabilities.update({
                "image_generation": True,
                "video_generation": True,
                "image_to_video": True,
                "advanced_prompts": True
            })
        
        return capabilities

class APIKeyManager:
    """Manages API keys for different services"""
    
    @classmethod
    def get_openai_key(cls) -> str:
        """Get OpenAI API key"""
        key = os.environ.get('OPENAI_API_KEY')
        if not key:
            logger.error("OPENAI_API_KEY not found in environment")
            raise ValueError("OpenAI API key not configured")
        return key
    
    @classmethod
    def get_google_key(cls) -> str:
        """Get Google API key for VEO"""
        key = os.environ.get('GOOGLE_API_KEY')
        if not key:
            logger.error("GOOGLE_API_KEY not found in environment")
            raise ValueError("Google API key not configured")
        return key
    
    @classmethod
    def get_pika_key(cls) -> str:
        """Get Pika Labs API key"""
        key = os.environ.get('PIKA_LABS_API_KEY')
        if not key:
            logger.error("PIKA_LABS_API_KEY not found in environment")
            raise ValueError("Pika Labs API key not configured")
        return key
    
    @classmethod
    def get_anthropic_key(cls) -> str:
        """Get Anthropic API key for quality assessment"""
        key = os.environ.get('ANTHROPIC_API_KEY')
        if not key:
            logger.error("ANTHROPIC_API_KEY not found in environment")
            raise ValueError("Anthropic API key not configured")
        return key
    
    @classmethod
    def check_service_availability(cls) -> Dict[str, bool]:
        """Check which services are available based on API keys"""
        services = {}
        
        try:
            cls.get_openai_key()
            services['openai'] = True
        except ValueError:
            services['openai'] = False
        
        try:
            cls.get_google_key()
            services['google'] = True
        except ValueError:
            services['google'] = False
        
        try:
            cls.get_pika_key()
            services['pika_labs'] = True
        except ValueError:
            services['pika_labs'] = False
        
        try:
            cls.get_anthropic_key()
            services['anthropic'] = True
        except ValueError:
            services['anthropic'] = False
        
        return services