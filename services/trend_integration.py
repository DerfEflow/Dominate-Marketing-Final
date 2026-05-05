"""
Trend Integration Service
Enhances AI prompts with current trends, data, and cultural references
"""

import logging
from datetime import datetime
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class TrendIntegrationService:
    """Service to integrate current trends and data into campaign content"""
    
    def __init__(self):
        self.current_year = datetime.now().year
        self.current_trends = self._get_current_trends()
        
    def enhance_prompt_with_trends(self, base_prompt: str, industry: str, brand_voice: str) -> str:
        """Enhance base prompt with industry-specific trends and cultural data"""
        
        trend_context = self._get_trend_context(industry, brand_voice)
        
        enhanced_prompt = f"""
        {base_prompt}
        
        CURRENT TREND INTEGRATION (MANDATORY):
        {trend_context}
        
        CONTENT FRESHNESS REQUIREMENTS:
        - Reference specific 2024-2025 industry developments
        - Include current cultural moments or viral concepts
        - Use contemporary language and references
        - Mention recent market shifts or consumer behavior changes
        - Incorporate platform-specific trends (TikTok, LinkedIn, Instagram formats)
        - Reference current technology adoption patterns
        - Use data points from the last 12 months
        
        UNIQUENESS CHECKLIST:
        ✓ Does this reference current events/trends?
        ✓ Does this include specific industry data?
        ✓ Would this make someone stop scrolling?
        ✓ Is this something only an insider would know?
        ✓ Does this challenge a common assumption?
        ✓ Would this get shared in industry Slack channels?
        """
        
        return enhanced_prompt
    
    def _get_current_trends(self) -> Dict[str, List[str]]:
        """Get current trends across different categories"""
        return {
            "technology": [
                "AI automation replacing manual processes",
                "Remote work optimization tools",
                "Cybersecurity for small businesses",
                "No-code/low-code solutions",
                "Sustainable tech adoption"
            ],
            "marketing": [
                "Short-form video dominance (TikTok, Reels)",
                "Authentic brand storytelling",
                "User-generated content campaigns", 
                "Micro-influencer partnerships",
                "Privacy-first marketing strategies"
            ],
            "business": [
                "Hybrid work models",
                "Supply chain resilience",
                "Customer experience automation",
                "Subscription business models",
                "ESG (Environmental, Social, Governance) focus"
            ],
            "culture": [
                "Mental health awareness",
                "Work-life integration",
                "Sustainability consciousness",
                "Digital minimalism",
                "Community-driven brands"
            ]
        }
    
    def _get_trend_context(self, industry: str, brand_voice: str) -> str:
        """Get industry and voice-specific trend context"""
        
        # Industry-specific insights
        industry_context = self._get_industry_context(industry.lower())
        
        # Voice-specific trend adaptation
        voice_context = self._get_voice_specific_trends(brand_voice)
        
        return f"""
        INDUSTRY CONTEXT ({industry}):
        {industry_context}
        
        BRAND VOICE TREND ADAPTATION ({brand_voice}):
        {voice_context}
        
        CURRENT MARKET DYNAMICS:
        - Consumer attention spans: 8 seconds average
        - Video content gets 1200% more shares than text+images
        - 73% of consumers prefer brands that take stands on issues
        - Mobile-first consumption: 85% of content viewed on mobile
        - Trust factor: User reviews 12x more trusted than brand content
        """
    
    def _get_industry_context(self, industry: str) -> str:
        """Get specific context for different industries"""
        
        industry_insights = {
            "technology": """
                - AI adoption increased 270% in 2024
                - 65% of businesses lack cybersecurity for remote work
                - No-code solutions market grew 50% year-over-year
                - Cloud migration accelerated post-pandemic
                - Data privacy regulations getting stricter globally
            """,
            
            "healthcare": """
                - Telehealth usage stabilized at 40x pre-pandemic levels
                - Mental health services demand increased 300%
                - Wearable health tech adoption hit mainstream
                - Healthcare staff shortage critical (2M openings)
                - Patient experience expectations mirror consumer apps
            """,
            
            "finance": """
                - Digital payment adoption reached 80% of transactions
                - Crypto regulation clarity emerging in 2024-2025
                - Buy-now-pay-later services maturing
                - AI fraud detection becoming standard
                - Financial wellness programs employee priority
            """,
            
            "e-commerce": """
                - Social commerce growing 35% annually
                - Same-day delivery now customer expectation
                - Sustainability influences 67% of purchase decisions
                - Live shopping events driving engagement
                - Return rates stabilizing around 30% for online
            """,
            
            "education": """
                - Hybrid learning models now permanent
                - Skill-based hiring trending over degree requirements
                - Microlearning and bite-sized content preferred
                - VR/AR adoption in training accelerating
                - Continuing education market exploding
            """,
            
            "real_estate": """
                - Virtual tours became standard (not optional)
                - Hybrid work changed commercial real estate forever
                - Mortgage rates volatility affecting buying patterns
                - PropTech adoption accelerated significantly
                - Sustainability features driving property values
            """
        }
        
        return industry_insights.get(industry, """
            - Digital transformation accelerating across all sectors
            - Customer experience expectations rising rapidly
            - Sustainability becoming competitive advantage
            - Remote/hybrid work reshaping business operations
            - Data privacy and security top business concerns
        """)
    
    def _get_voice_specific_trends(self, brand_voice: str) -> str:
        """Get trend adaptations for specific brand voices"""
        
        voice_trends = {
            "edgy": """
                - Use current controversies as conversation starters
                - Reference recent industry failures or scandals
                - Leverage polarizing topics for engagement
                - Challenge sacred cows in your industry
                - Use provocative comparisons to current events
            """,
            
            "roast": """
                - Reference recent corporate fails or viral mistakes
                - Use current memes and internet culture
                - Mock outdated industry practices with recent examples
                - Reference competitor missteps from last 6 months
                - Use absurd analogies to current pop culture
            """,
            
            "professional": """
                - Reference recent industry reports and statistics
                - Mention current regulatory changes or compliance updates
                - Use recent case studies and success stories
                - Reference thought leaders and recent insights
                - Include current market analysis and projections
            """,
            
            "witty": """
                - Use current memes and viral content appropriately
                - Reference recent pop culture moments
                - Make clever connections to trending topics
                - Use contemporary humor and language
                - Reference current social media phenomena
            """
        }
        
        return voice_trends.get(brand_voice, """
            - Stay current with industry news and developments
            - Reference recent market changes and opportunities
            - Use contemporary language and expressions
            - Include current consumer behavior insights
        """)
    
    def get_content_quality_enhancers(self) -> List[str]:
        """Get specific elements that make content stand out"""
        return [
            "Specific industry statistics from 2024-2025",
            "References to current events or cultural moments", 
            "Contrarian viewpoints that challenge industry norms",
            "Insider knowledge that competitors miss",
            "Data points that surprise the target audience",
            "Cultural references that create instant connection",
            "Platform-specific content adaptations",
            "Current technology or social media trends as hooks",
            "Recent market failures or success stories as examples",
            "Unexpected analogies or memorable comparisons"
        ]