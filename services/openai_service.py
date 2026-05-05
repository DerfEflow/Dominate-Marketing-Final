"""
OpenAI Service Integration
Handles GPT-5 and GPT-5-mini for text content and image generation
"""
import os
import json
import logging
from typing import Dict, Any, Optional, List
from openai import OpenAI
from models import SubscriptionTier
from .ai_models import ModelConfig, APIKeyManager, AIProvider
from services.content_enhancer import ContentEnhancementService
from services.trend_discovery import TrendDiscoveryService

logger = logging.getLogger(__name__)

class OpenAIService:
    """OpenAI service for text and image generation"""
    
    def __init__(self):
        self.client = OpenAI(api_key=APIKeyManager.get_openai_key())
        self.content_enhancer = ContentEnhancementService()
        self.trend_discovery = TrendDiscoveryService()
    
    def generate_campaign_content(self, 
                                business_data: Dict[str, Any], 
                                subscription_tier: SubscriptionTier,
                                campaign_goal: str = "leads",
                                target_audience: str = "",
                                brand_voice: str = "professional",
                                include_trends: bool = False,
                                trend_types: List[str] = None) -> Dict[str, Any]:
        """
        Generate comprehensive campaign content based on business data
        Uses GPT-5 for premium tiers, GPT-5-mini for cost savings on lower tiers
        """
        
        model = ModelConfig.get_model_for_tier(AIProvider.OPENAI, subscription_tier)
        capabilities = ModelConfig.get_tier_capabilities(subscription_tier)
        
        logger.info(f"Generating campaign content with {model} for {subscription_tier.value} tier")
        
        # Discover viral trends if requested
        viral_trends = []
        trend_context = ""
        if include_trends:
            industry = business_data.get('industry', 'general business')
            try:
                viral_trends = self.trend_discovery.discover_viral_trends(industry, target_audience)
                if viral_trends:
                    trend_suggestions = self.trend_discovery.get_trend_integration_suggestions(
                        viral_trends[:3], campaign_goal, brand_voice
                    )
                    trend_context = self._build_trend_integration_context(trend_suggestions)
                    logger.info(f"Integrated {len(viral_trends)} viral trends into campaign")
            except Exception as e:
                logger.warning(f"Failed to discover trends: {e}")
        
        # Build comprehensive prompt with uniqueness enhancement
        base_prompt = self._build_content_generation_prompt(
            business_data, campaign_goal, target_audience, brand_voice, capabilities, trend_context
        )
        
        # Enhance for unique, viral content
        industry = business_data.get('industry', 'general business')
        prompt = self.content_enhancer.enhance_content_prompt(base_prompt, industry, brand_voice)
        
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert viral marketing strategist. Generate high-converting marketing content that dominates competitors and captures market attention. Focus on trends from the last 6 hours, not outdated strategies."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.8,  # Creative but focused
                max_tokens=4000
            )
            
            content = json.loads(response.choices[0].message.content)
            
            # Add metadata
            content['model_used'] = model
            content['tier'] = subscription_tier.value
            content['capabilities'] = capabilities
            content['viral_trends_used'] = viral_trends if include_trends else []
            content['trend_integration'] = include_trends
            
            return content
            
        except Exception as e:
            logger.error(f"Error generating campaign content: {str(e)}")
            raise Exception(f"Failed to generate campaign content: {str(e)}")
    
    def generate_image_prompts(self, 
                             campaign_content: Dict[str, Any],
                             subscription_tier: SubscriptionTier,
                             image_count: int = 3) -> List[Dict[str, Any]]:
        """Generate detailed image prompts for visual content"""
        
        model = ModelConfig.get_model_for_tier(AIProvider.OPENAI, subscription_tier)
        
        prompt = f"""
        Based on this campaign content, create {image_count} detailed image generation prompts:
        
        Campaign: {campaign_content.get('title', 'Untitled')}
        Message: {campaign_content.get('main_message', '')}
        Target Audience: {campaign_content.get('target_audience', '')}
        
        Generate prompts that:
        1. Align with the campaign message
        2. Appeal to the target audience
        3. Follow current visual trends
        4. Are optimized for social media
        5. Include specific style, lighting, and composition details
        
        Return as JSON array with objects containing:
        - prompt: Detailed image generation prompt
        - style: Visual style description
        - purpose: How this image supports the campaign
        - platform: Best social platform for this image
        """
        
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert visual content strategist. Create detailed, trend-aware image prompts that convert viewers into customers."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.9,  # High creativity for visual concepts
                max_tokens=2000
            )
            
            result = json.loads(response.choices[0].message.content)
            return result.get('image_prompts', [])
            
        except Exception as e:
            logger.error(f"Error generating image prompts: {str(e)}")
            raise Exception(f"Failed to generate image prompts: {str(e)}")
    
    def generate_video_script(self, 
                            campaign_content: Dict[str, Any],
                            subscription_tier: SubscriptionTier,
                            video_length: str = "30s") -> Dict[str, Any]:
        """Generate video script and scene descriptions"""
        
        model = ModelConfig.get_model_for_tier(AIProvider.OPENAI, subscription_tier)
        
        prompt = f"""
        Create a {video_length} viral video script based on this campaign:
        
        Campaign: {campaign_content.get('title', 'Untitled')}
        Message: {campaign_content.get('main_message', '')}
        Call to Action: {campaign_content.get('cta', '')}
        
        Generate a complete video production package:
        1. Hook (first 3 seconds)
        2. Problem/Pain Point (seconds 3-10)
        3. Solution/Product Introduction (seconds 10-20)
        4. Social Proof/Benefits (seconds 20-27)
        5. Strong Call to Action (seconds 27-30)
        
        Include:
        - Voiceover script with timing
        - Visual scene descriptions
        - Text overlays
        - Music/sound cues
        - Transition effects
        
        Format for modern social media (vertical video, attention-grabbing)
        
        Return as JSON with structured scenes.
        """
        
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a viral video strategist who creates scripts that stop scrolling and drive action. Focus on psychological triggers and current content trends."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.8,
                max_tokens=3000
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"Error generating video script: {str(e)}")
            raise Exception(f"Failed to generate video script: {str(e)}")
    
    def _build_trend_integration_context(self, trend_suggestions: List[Dict[str, Any]]) -> str:
        """Build context for trend integration"""
        
        if not trend_suggestions:
            return ""
        
        context = "\n🔥 VIRAL TRENDS TO INTEGRATE:\n"
        
        for suggestion in trend_suggestions:
            trend = suggestion['trend']
            context += f"""
TREND: {trend['title']}
Type: {trend['type']}
Viral Factor: {trend['viral_factor']}
Usage Tip: {trend['usage_tip']}
Integration Approach: {suggestion['integration_approach']}
Content Ideas: {', '.join(suggestion['content_ideas'][:2])}
Copy Angles: {', '.join(suggestion['copy_angles'][:2])}
"""
        
        context += "\nCREATIVELY INCORPORATE THE MOST RELEVANT TREND INTO YOUR CAMPAIGN CONTENT FOR MAXIMUM VIRAL POTENTIAL.\n"
        return context

    def _build_content_generation_prompt(self, 
                                       business_data: Dict[str, Any],
                                       campaign_goal: str,
                                       target_audience: str,
                                       brand_voice: str,
                                       capabilities: Dict[str, bool],
                                       trend_context: str = "") -> str:
        """Build comprehensive prompt for content generation"""
        
        # Enhanced brand voice instructions
        voice_instructions = self._get_brand_voice_instructions(brand_voice)
        
        prompt = f"""
        Analyze this business and create a VIRAL marketing campaign that stands out from generic agency work:
        
        BUSINESS DATA:
        - URL: {business_data.get('business_url', '')}
        - Description: {business_data.get('description', '')}
        - Industry: {business_data.get('industry', '')}
        - Products/Services: {business_data.get('products', '')}
        
        CAMPAIGN REQUIREMENTS:
        - Goal: {campaign_goal}
        - Target Audience: {target_audience or 'General audience'}
        - Brand Voice: {brand_voice}
        
        BRAND VOICE INSTRUCTIONS:
        {voice_instructions}
        
        {trend_context}
        
        UNIQUENESS REQUIREMENTS (CRITICAL):
        - Include relevant industry statistics, trends, or data points from 2024-2025
        - Reference current cultural moments, memes, or trending topics
        - Incorporate unexpected angles or contrarian viewpoints
        - Use specific, memorable analogies or comparisons
        - Include industry-specific pain points that competitors ignore
        - Reference actual market failures or success stories
        - Use current technology or social media trends as hooks
        - Create content that makes people say "I never thought of it that way"
        
        CONTENT MUST BE:
        - Instantly recognizable as unique (not generic agency copy)
        - Packed with specific insights, not broad statements
        - Shareable because it's genuinely interesting or surprising
        - Based on real market dynamics and customer behaviors
        - Timely and relevant to current events/trends
        
        CAPABILITIES FOR THIS TIER:
        {json.dumps(capabilities, indent=2)}
        
        Generate a complete campaign package including:
        
        1. CAMPAIGN ANALYSIS:
           - Market opportunity
           - Competitor gaps
           - Trending angles (from last 6 hours)
           - Viral potential score
        
        2. CORE CONTENT:
           - Compelling campaign title
           - Main marketing message
           - 3 variations of ad copy (short, medium, long)
           - Strong call-to-action
           - Hashtag strategy
        
        3. AUDIENCE TARGETING:
           - Primary audience profile
           - Pain points addressed
           - Psychological triggers used
           - Platform recommendations
        
        4. CONTENT STRATEGY:
           - Post timing recommendations
           - Content variations for different platforms
           - Engagement optimization tips
        
        Return as structured JSON with all sections clearly labeled.
        Focus on content that converts viewers into customers.
        """
        
        return prompt
    
    def _get_brand_voice_instructions(self, brand_voice: str) -> str:
        """Get specific instructions for different brand voices"""
        
        voice_guide = {
            "professional": """
                - Use authoritative, expert tone
                - Focus on credibility and trust
                - Highlight qualifications and results
                - Avoid slang or casual language
                - Emphasize reliability and competence
            """,
            
            "witty": """
                - Use clever wordplay and humor
                - Include smart observations and insights
                - Make content entertaining while informative
                - Use pop culture references appropriately
                - Keep humor light and accessible
            """,
            
            "casual": """
                - Write like talking to a friend
                - Use everyday language and expressions
                - Be relatable and down-to-earth
                - Include personal touches and stories
                - Avoid overly formal language
            """,
            
            "edgy": """
                - Push boundaries with bold, provocative language that makes people take notice
                - Use dark humor, sharp wit, and unexpected angles
                - Challenge conventional thinking and call out industry BS
                - Include content that might make people blush or do a double-take
                - Ride the line between shocking and professional - fearless but not offensive
                - Use mild controversy and taboo topics to capture attention
                - Be the brand that says what everyone else is thinking but afraid to say
                - Examples: 
                  * "While everyone else is playing it safe, we're breaking all the boring rules"
                  * "Other companies won't tell you this, but we will..."
                  * "The truth [industry] doesn't want you to know"
                - Think: What would make someone screenshot this and send it to their friends?
            """,
            
            "roast": """
                - Hilariously roast the current market state and competitors
                - Put the entire industry in ridiculously bad light with comedic exaggeration
                - Be brutally honest about how broken current solutions are
                - Use humor to highlight absurd industry failures and outdated practices
                - Then position the client's product as the obvious hero solution
                - Structure: Problem roast → Market roast → Hero entrance
                - Examples: 
                  * "The [industry] is more broken than a Nokia phone trying to run TikTok"
                  * "Most [competitors] are solving 2024 problems with 1995 solutions"
                  * "If [current market] was a movie, it would be called 'How to Disappoint Customers in 10 Easy Steps'"
                - Make it so hilariously accurate that people share it while being completely convinced
                - End with the client as the obvious solution that fixes everything
            """,
            
            "confident": """
                - Use bold, assertive language
                - Show complete confidence in the product
                - Use strong action words and declarations
                - Position as the obvious best choice
                - No hesitation or qualification in statements
            """
        }
        
        return voice_guide.get(brand_voice, voice_guide["professional"])