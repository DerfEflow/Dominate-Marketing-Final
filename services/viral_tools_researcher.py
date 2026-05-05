"""
Viral Tools Researcher - Discovers viral content opportunities
Researches viral trends in priority order for campaign creation
"""

import logging
import requests
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import json

# Import trend analysis if available
try:
    from pytrends.request import TrendReq
    PYTRENDS_AVAILABLE = True
except ImportError:
    PYTRENDS_AVAILABLE = False
    logging.warning("pytrends not available - Google Trends analysis will be limited")

logger = logging.getLogger(__name__)

@dataclass
class ViralTool:
    """Individual viral trend or meme that can be used for marketing"""
    type: str  # 'industry_trend', 'viral_trend', 'viral_meme'
    title: str
    description: str
    relevance_score: float
    trending_score: float
    content_type: str  # 'text', 'image', 'video', 'audio'
    platform_fit: List[str]  # ['facebook', 'instagram', 'tiktok', 'twitter']
    usage_suggestions: List[str]
    metadata: Dict[str, Any]

@dataclass
class ViralToolsResearch:
    """Complete viral tools research results"""
    sell_profile_id: str
    industry_trends: List[ViralTool]
    popular_viral_trends: List[ViralTool]
    viral_memes: List[ViralTool]
    research_timestamp: str
    confidence_score: float

class ViralToolsResearcher:
    """Researches viral trends and memes for campaign creation"""
    
    def __init__(self):
        # Initialize trend analysis
        if PYTRENDS_AVAILABLE:
            self.pytrends = TrendReq(hl='en-US', tz=360)
        else:
            self.pytrends = None
        
        # Platform API configurations 
        self.region = os.getenv('REGION', 'US')
        self.country = os.getenv('COUNTRY', 'US')
        self.language = os.getenv('LANGUAGE', 'en')
        
        # Industry-specific trending topics
        self.industry_trend_keywords = {
            'construction': ['home renovation trends', 'sustainable building', 'smart home technology', 'energy efficient', 'modern design'],
            'healthcare': ['telehealth', 'wellness trends', 'mental health awareness', 'preventive care', 'health technology'],
            'legal': ['legal tech', 'online legal services', 'legal education', 'rights awareness', 'legal advice'],
            'automotive': ['electric vehicles', 'auto technology', 'car maintenance tips', 'vehicle safety', 'automotive innovation'],
            'restaurant': ['food trends', 'sustainable dining', 'food delivery', 'culinary innovation', 'healthy eating'],
            'retail': ['e-commerce trends', 'sustainable shopping', 'customer experience', 'retail technology', 'online shopping'],
            'technology': ['ai trends', 'digital transformation', 'cybersecurity', 'cloud computing', 'tech innovation'],
            'real_estate': ['housing market trends', 'home buying tips', 'real estate technology', 'property investment', 'market analysis'],
            'finance': ['fintech trends', 'investment strategies', 'financial planning', 'digital banking', 'financial literacy'],
            'beauty': ['beauty trends', 'skincare innovation', 'sustainable beauty', 'beauty technology', 'wellness beauty'],
            'fitness': ['fitness trends', 'home workouts', 'wellness technology', 'nutrition trends', 'mental wellness'],
            'education': ['edtech trends', 'online learning', 'educational innovation', 'skill development', 'learning technology']
        }
        
        # Current viral trend categories
        self.viral_trend_categories = [
            'social media challenges',
            'trending hashtags',
            'popular memes',
            'viral videos',
            'trending topics',
            'cultural moments',
            'seasonal trends',
            'technology trends',
            'lifestyle trends',
            'entertainment trends'
        ]
        
        # Viral meme templates and formats
        self.viral_meme_templates = [
            {'type': 'before_after', 'description': 'Before/After transformation posts', 'platforms': ['instagram', 'facebook', 'tiktok']},
            {'type': 'how_it_started', 'description': 'How it started vs How it\'s going format', 'platforms': ['twitter', 'instagram', 'facebook']},
            {'type': 'relatable_moments', 'description': 'Relatable customer experience memes', 'platforms': ['twitter', 'instagram', 'tiktok']},
            {'type': 'expectation_reality', 'description': 'Expectation vs Reality format', 'platforms': ['instagram', 'tiktok', 'facebook']},
            {'type': 'pov_content', 'description': 'POV (Point of View) style content', 'platforms': ['tiktok', 'instagram']},
            {'type': 'this_you', 'description': 'This you? calling out format', 'platforms': ['twitter', 'tiktok']},
            {'type': 'distracted_boyfriend', 'description': 'Distracted boyfriend meme template', 'platforms': ['facebook', 'instagram', 'twitter']},
            {'type': 'drake_pointing', 'description': 'Drake pointing meme format', 'platforms': ['instagram', 'facebook', 'twitter']},
            {'type': 'woman_yelling_cat', 'description': 'Woman yelling at cat meme format', 'platforms': ['facebook', 'instagram', 'twitter']},
            {'type': 'expanding_brain', 'description': 'Expanding brain intelligence levels', 'platforms': ['twitter', 'instagram', 'facebook']}
        ]
    
    def research_viral_tools(self, sell_profile: Dict[str, Any]) -> ViralToolsResearch:
        """Research all viral tools for a business sell profile"""
        logger.info(f"Starting viral tools research for {sell_profile.get('business_name')}")
        
        try:
            # Priority 1: Industry-specific viral trends
            industry_trends = self._research_industry_trends(
                sell_profile.get('industry', 'professional_services'),
                sell_profile.get('keywords', [])
            )
            
            # Priority 2: Popular viral trends (general)
            popular_trends = self._research_popular_viral_trends()
            
            # Priority 3: Viral memes for product/service highlighting
            viral_memes = self._research_viral_memes(
                sell_profile.get('industry'),
                sell_profile.get('distinctives', [])
            )
            
            # Calculate overall confidence
            confidence = self._calculate_research_confidence(
                industry_trends, popular_trends, viral_memes
            )
            
            research = ViralToolsResearch(
                sell_profile_id=sell_profile.get('url', ''),
                industry_trends=industry_trends,
                popular_viral_trends=popular_trends,
                viral_memes=viral_memes,
                research_timestamp=datetime.now().isoformat(),
                confidence_score=confidence
            )
            
            logger.info(f"Viral tools research completed with {confidence:.2f} confidence")
            return research
            
        except Exception as e:
            logger.error(f"Error in viral tools research: {e}")
            return self._create_fallback_research(sell_profile)
    
    def _research_industry_trends(self, industry: str, keywords: List[str]) -> List[ViralTool]:
        """Research trending topics specific to the business industry"""
        industry_trends = []
        
        # Get industry-specific keywords
        industry_keywords = self.industry_trend_keywords.get(industry, [])
        
        # Combine with business-specific keywords
        all_keywords = industry_keywords + keywords[:5]
        
        if self.pytrends and all_keywords:
            try:
                # Research trends for industry keywords in batches
                for i in range(0, len(all_keywords), 3):
                    batch = all_keywords[i:i+3]
                    
                    try:
                        # Build payload for Google Trends
                        self.pytrends.build_payload(
                            batch,
                            timeframe='now 30-d',
                            geo=self.country
                        )
                        
                        # Get interest over time
                        interest_data = self.pytrends.interest_over_time()
                        
                        if not interest_data.empty:
                            for keyword in batch:
                                if keyword in interest_data.columns:
                                    avg_interest = interest_data[keyword].mean()
                                    
                                    if avg_interest > 10:  # Only include trending keywords
                                        trend = ViralTool(
                                            type='industry_trend',
                                            title=f"{keyword.title()} Trend",
                                            description=f"Rising trend in {industry} industry: {keyword}",
                                            relevance_score=0.9,  # High relevance for industry trends
                                            trending_score=min(avg_interest / 100, 1.0),
                                            content_type='text',
                                            platform_fit=['facebook', 'instagram', 'linkedin'],
                                            usage_suggestions=[
                                                f"Create content around {keyword} in {industry}",
                                                f"Position business as expert in {keyword}",
                                                f"Use {keyword} hashtags in posts"
                                            ],
                                            metadata={
                                                'keyword': keyword,
                                                'industry': industry,
                                                'avg_interest': avg_interest,
                                                'data_source': 'google_trends'
                                            }
                                        )
                                        industry_trends.append(trend)
                        
                        # Get related queries
                        related_queries = self.pytrends.related_queries()
                        for keyword, queries_data in related_queries.items():
                            if queries_data and 'rising' in queries_data:
                                rising_df = queries_data['rising']
                                if rising_df is not None and not rising_df.empty:
                                    for _, row in rising_df.head(3).iterrows():
                                        trend = ViralTool(
                                            type='industry_trend',
                                            title=f"Rising: {row['query']}",
                                            description=f"Rising search trend related to {keyword}",
                                            relevance_score=0.8,
                                            trending_score=min(int(row['value']) / 1000, 1.0),
                                            content_type='text',
                                            platform_fit=['facebook', 'instagram', 'twitter'],
                                            usage_suggestions=[
                                                f"Create content answering '{row['query']}'",
                                                f"Use '{row['query']}' as blog topic",
                                                f"Target '{row['query']}' in ad campaigns"
                                            ],
                                            metadata={
                                                'base_keyword': keyword,
                                                'rising_value': int(row['value']),
                                                'query_type': 'rising',
                                                'data_source': 'google_trends'
                                            }
                                        )
                                        industry_trends.append(trend)
                    
                    except Exception as batch_error:
                        logger.error(f"Error processing trend batch: {batch_error}")
                        continue
                        
            except Exception as e:
                logger.error(f"Error in industry trends research: {e}")
        
        # Add fallback industry trends if no data found
        if not industry_trends and industry in self.industry_trend_keywords:
            for keyword in self.industry_trend_keywords[industry][:3]:
                trend = ViralTool(
                    type='industry_trend',
                    title=f"{keyword.title()} Focus",
                    description=f"Key trend area in {industry}: {keyword}",
                    relevance_score=0.7,
                    trending_score=0.6,
                    content_type='text',
                    platform_fit=['facebook', 'instagram', 'linkedin'],
                    usage_suggestions=[
                        f"Create educational content about {keyword}",
                        f"Show expertise in {keyword}",
                        f"Use {keyword} in marketing messaging"
                    ],
                    metadata={
                        'keyword': keyword,
                        'industry': industry,
                        'data_source': 'fallback'
                    }
                )
                industry_trends.append(trend)
        
        return industry_trends[:8]  # Limit to top 8 trends
    
    def _research_popular_viral_trends(self) -> List[ViralTool]:
        """Research popular viral trends not necessarily industry-specific"""
        popular_trends = []
        
        # Current viral trend keywords to research
        viral_keywords = [
            'viral content', 'trending now', 'social media trends', 
            'popular hashtags', 'viral videos', 'trending topics'
        ]
        
        if self.pytrends:
            try:
                # Research general viral trends
                self.pytrends.build_payload(
                    viral_keywords[:3],
                    timeframe='now 7-d',
                    geo=self.country
                )
                
                interest_data = self.pytrends.interest_over_time()
                
                if not interest_data.empty:
                    for keyword in viral_keywords[:3]:
                        if keyword in interest_data.columns:
                            avg_interest = interest_data[keyword].mean()
                            
                            trend = ViralTool(
                                type='viral_trend',
                                title=f"{keyword.title()}",
                                description=f"Currently trending: {keyword}",
                                relevance_score=0.6,  # Medium relevance
                                trending_score=min(avg_interest / 100, 1.0),
                                content_type='mixed',
                                platform_fit=['tiktok', 'instagram', 'twitter', 'facebook'],
                                usage_suggestions=[
                                    f"Jump on {keyword} bandwagon",
                                    f"Create content that leverages {keyword}",
                                    f"Use popular formats from {keyword}"
                                ],
                                metadata={
                                    'keyword': keyword,
                                    'avg_interest': avg_interest,
                                    'data_source': 'google_trends'
                                }
                            )
                            popular_trends.append(trend)
                            
            except Exception as e:
                logger.error(f"Error researching popular trends: {e}")
        
        # Add current social media trending formats
        trending_formats = [
            {
                'title': 'Short-Form Video Content',
                'description': 'Quick, engaging videos under 60 seconds',
                'platforms': ['tiktok', 'instagram', 'youtube'],
                'score': 0.9
            },
            {
                'title': 'Behind-The-Scenes Content',
                'description': 'Showing the real process and people behind the business',
                'platforms': ['instagram', 'tiktok', 'facebook'],
                'score': 0.8
            },
            {
                'title': 'User-Generated Content',
                'description': 'Content created by customers and fans',
                'platforms': ['instagram', 'tiktok', 'facebook'],
                'score': 0.85
            },
            {
                'title': 'Educational Carousel Posts',
                'description': 'Multi-slide educational content that teaches',
                'platforms': ['instagram', 'linkedin', 'facebook'],
                'score': 0.7
            }
        ]
        
        for format_data in trending_formats:
            trend = ViralTool(
                type='viral_trend',
                title=format_data['title'],
                description=format_data['description'],
                relevance_score=0.7,
                trending_score=format_data['score'],
                content_type='video' if 'video' in format_data['title'].lower() else 'mixed',
                platform_fit=format_data['platforms'],
                usage_suggestions=[
                    f"Create {format_data['title'].lower()} for your business",
                    f"Adapt existing content to {format_data['title'].lower()} format",
                    f"Plan weekly {format_data['title'].lower()} content"
                ],
                metadata={
                    'format_type': format_data['title'].lower().replace(' ', '_'),
                    'data_source': 'platform_analysis'
                }
            )
            popular_trends.append(trend)
        
        return popular_trends
    
    def _research_viral_memes(self, industry: str, distinctives: List[str]) -> List[ViralTool]:
        """Research viral memes that can highlight products/services"""
        viral_memes = []
        
        # Generate memes based on templates
        for template in self.viral_meme_templates:
            # Create industry-specific meme suggestions
            meme_suggestions = self._generate_meme_suggestions(
                template, industry, distinctives
            )
            
            meme = ViralTool(
                type='viral_meme',
                title=template['description'],
                description=f"Use {template['type']} format to highlight your business",
                relevance_score=0.5,  # Memes have medium relevance but high engagement
                trending_score=0.8,   # Memes tend to be highly engaging
                content_type='image',
                platform_fit=template['platforms'],
                usage_suggestions=meme_suggestions,
                metadata={
                    'meme_type': template['type'],
                    'template_name': template['description'],
                    'industry_applied': industry
                }
            )
            viral_memes.append(meme)
        
        return viral_memes[:6]  # Limit to top 6 meme formats
    
    def _generate_meme_suggestions(self, template: Dict, industry: str, distinctives: List[str]) -> List[str]:
        """Generate specific meme usage suggestions for business"""
        suggestions = []
        
        if template['type'] == 'before_after':
            suggestions = [
                f"Show before/after results of your {industry} services",
                "Customer transformation stories",
                "Workspace/project transformation photos"
            ]
        elif template['type'] == 'how_it_started':
            suggestions = [
                "Company founding story vs current success",
                "First project vs latest achievement",
                "Business growth journey"
            ]
        elif template['type'] == 'relatable_moments':
            suggestions = [
                f"Relatable {industry} customer experiences",
                "Common customer pain points you solve",
                "Industry-specific humor and situations"
            ]
        elif template['type'] == 'expectation_reality':
            suggestions = [
                "Customer expectations vs amazing results",
                "Competitor promises vs your delivery",
                "DIY attempts vs professional service"
            ]
        elif template['type'] == 'pov_content':
            suggestions = [
                f"POV: You found the best {industry} service",
                "POV: Your problem is finally solved",
                "POV: You chose quality over cheap"
            ]
        else:
            # Generic suggestions for other templates
            suggestions = [
                f"Apply to {industry} customer scenarios",
                "Use for service comparisons",
                "Highlight business advantages"
            ]
        
        return suggestions
    
    def _calculate_research_confidence(self, industry_trends: List[ViralTool], 
                                     popular_trends: List[ViralTool], 
                                     viral_memes: List[ViralTool]) -> float:
        """Calculate confidence score for research quality"""
        score = 0.0
        
        # Industry trends quality (0-0.4)
        if len(industry_trends) >= 5:
            score += 0.4
        elif len(industry_trends) >= 3:
            score += 0.3
        elif len(industry_trends) >= 1:
            score += 0.2
        
        # Popular trends quality (0-0.3)
        if len(popular_trends) >= 4:
            score += 0.3
        elif len(popular_trends) >= 2:
            score += 0.2
        elif len(popular_trends) >= 1:
            score += 0.1
        
        # Viral memes availability (0-0.3)
        if len(viral_memes) >= 5:
            score += 0.3
        elif len(viral_memes) >= 3:
            score += 0.2
        elif len(viral_memes) >= 1:
            score += 0.1
        
        return min(score, 1.0)
    
    def _create_fallback_research(self, sell_profile: Dict[str, Any]) -> ViralToolsResearch:
        """Create fallback research when APIs fail"""
        industry = sell_profile.get('industry', 'professional_services')
        
        # Basic industry trends
        industry_trends = [
            ViralTool(
                type='industry_trend',
                title=f"{industry.title()} Excellence",
                description=f"Focus on quality and expertise in {industry}",
                relevance_score=0.8,
                trending_score=0.6,
                content_type='text',
                platform_fit=['facebook', 'instagram', 'linkedin'],
                usage_suggestions=[
                    f"Showcase {industry} expertise",
                    "Share quality work examples",
                    "Educate about industry standards"
                ],
                metadata={'data_source': 'fallback'}
            )
        ]
        
        # Basic viral trends
        popular_trends = [
            ViralTool(
                type='viral_trend',
                title='Short-Form Video Content',
                description='Quick, engaging videos under 60 seconds',
                relevance_score=0.7,
                trending_score=0.9,
                content_type='video',
                platform_fit=['tiktok', 'instagram'],
                usage_suggestions=[
                    "Create quick service demos",
                    "Show before/after results",
                    "Share quick tips"
                ],
                metadata={'data_source': 'fallback'}
            )
        ]
        
        # Basic memes
        viral_memes = [
            ViralTool(
                type='viral_meme',
                title='Before/After Format',
                description='Show transformation results',
                relevance_score=0.6,
                trending_score=0.8,
                content_type='image',
                platform_fit=['instagram', 'facebook'],
                usage_suggestions=[
                    "Show service transformations",
                    "Highlight improvements",
                    "Customer success stories"
                ],
                metadata={'data_source': 'fallback'}
            )
        ]
        
        return ViralToolsResearch(
            sell_profile_id=sell_profile.get('url', ''),
            industry_trends=industry_trends,
            popular_viral_trends=popular_trends,
            viral_memes=viral_memes,
            research_timestamp=datetime.now().isoformat(),
            confidence_score=0.4
        )
    
    def export_research(self, research: ViralToolsResearch) -> Dict[str, Any]:
        """Export research as dictionary for API responses"""
        return asdict(research)