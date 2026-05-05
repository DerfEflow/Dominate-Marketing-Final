"""
AI Strategy Generator using latest OpenAI models
Creates comprehensive marketing strategies based on authentic business data
"""

import logging
import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from openai import OpenAI

logger = logging.getLogger(__name__)

class AIStrategyGenerator:
    """
    Generates marketing strategies using latest OpenAI models
    Uses authentic data only - no synthetic content
    """
    
    def __init__(self):
        self.api_key = os.environ.get('OPENAI_API_KEY')
        if not self.api_key:
            raise Exception("OpenAI API key not configured")
            
        self.client = OpenAI(api_key=self.api_key)
        
        # Latest available models - user confirmed access to newest models
        self.strategy_model = "gpt-4o"  # For comprehensive strategy generation
        self.prompt_model = "gpt-4o-mini"  # For prompt generation tasks
    
    def generate_marketing_strategy(self, 
                                  business_data: Dict[str, Any], 
                                  competitor_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate comprehensive marketing strategy using authentic business data
        """
        logger.info(f"Generating marketing strategy for {business_data['business_name']}")
        
        # Prepare authentic data context
        strategy_context = self._prepare_strategy_context(business_data, competitor_data)
        
        try:
            strategy_prompt = self._create_strategy_prompt(strategy_context)
            
            response = self.client.chat.completions.create(
                model=self.strategy_model,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are an expert marketing strategist. Create comprehensive, actionable marketing strategies based ONLY on the provided authentic business data. Do not invent or assume information not present in the data. Respond with valid JSON only."
                    },
                    {
                        "role": "user", 
                        "content": strategy_prompt
                    }
                ],
                max_tokens=3000,
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            strategy_text = response.choices[0].message.content
            strategy = json.loads(strategy_text)
            
            # Add metadata
            strategy['generated_at'] = datetime.now().isoformat()
            strategy['model_used'] = self.strategy_model
            strategy['based_on_authentic_data'] = True
            strategy['source_business'] = business_data['business_name']
            
            logger.info("Marketing strategy generated successfully")
            return strategy
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse strategy JSON: {e}")
            raise Exception("Strategy generation returned invalid format")
        except Exception as e:
            logger.error(f"Strategy generation failed: {e}")
            raise Exception(f"Failed to generate marketing strategy: {str(e)}")
    
    def generate_content_prompts(self, strategy: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate specific content prompts based on marketing strategy
        """
        logger.info("Generating content creation prompts")
        
        try:
            prompt_request = self._create_prompt_generation_request(strategy)
            
            response = self.client.chat.completions.create(
                model=self.prompt_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a content strategist. Generate specific, actionable content prompts based on the marketing strategy. Return valid JSON only with exact structure requested."
                    },
                    {
                        "role": "user",
                        "content": prompt_request
                    }
                ],
                max_tokens=2000,
                temperature=0.8,
                response_format={"type": "json_object"}
            )
            
            prompts_text = response.choices[0].message.content
            content_prompts = json.loads(prompts_text)
            
            # Add metadata
            content_prompts['generated_at'] = datetime.now().isoformat()
            content_prompts['model_used'] = self.prompt_model
            content_prompts['strategy_based'] = True
            
            logger.info("Content prompts generated successfully")
            return content_prompts
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse content prompts JSON: {e}")
            raise Exception("Content prompt generation returned invalid format")
        except Exception as e:
            logger.error(f"Content prompt generation failed: {e}")
            raise Exception(f"Failed to generate content prompts: {str(e)}")
    
    def _prepare_strategy_context(self, business_data: Dict[str, Any], competitor_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Prepare context for strategy generation using only authentic data"""
        context = {
            'business': {
                'name': business_data['business_name'],
                'industry': business_data['industry'],
                'description': business_data['description'],
                'services': business_data.get('services_products', []),
                'location': business_data.get('location_indicators', {}),
                'keywords': business_data.get('keywords', []),
                'content_length': business_data.get('content_length', 0)
            },
            'competitors': [
                {
                    'name': comp.get('name', ''),
                    'description': comp.get('description', ''),
                    'url': comp.get('url', '')
                } for comp in competitor_data[:3]  # Top 3 competitors
            ],
            'market_context': {
                'total_competitors_found': len(competitor_data),
                'data_source': 'authentic_web_scraping'
            }
        }
        
        return context
    
    def _create_strategy_prompt(self, context: Dict[str, Any]) -> str:
        """Create strategy generation prompt based on authentic data"""
        return f"""
Based ONLY on this authentic business data, create a comprehensive marketing strategy:

BUSINESS DATA:
- Name: {context['business']['name']}
- Industry: {context['business']['industry']}
- Description: {context['business']['description']}
- Services: {', '.join(context['business']['services']) if context['business']['services'] else 'Not specified'}
- Keywords: {', '.join(context['business']['keywords']) if context['business']['keywords'] else 'Not specified'}
- Content Depth: {context['business']['content_length']} characters of authentic content

COMPETITOR LANDSCAPE:
{chr(10).join([f"- {comp['name']}: {comp['description']}" for comp in context['competitors']])}
Total competitors found: {context['market_context']['total_competitors_found']}

Create a marketing strategy in this exact JSON format:
{{
    "target_audience": {{
        "primary": "Based on business description and industry",
        "secondary": "Additional audience if applicable",
        "demographics": "Age, interests, behavior patterns"
    }},
    "value_proposition": "Unique value based on actual business description",
    "competitive_positioning": "How to position against the actual competitors found",
    "content_strategy": {{
        "image_approach": "Visual content strategy for this specific business",
        "video_approach": "Video content strategy based on business type",
        "text_approach": "Written content strategy for the identified audience"
    }},
    "key_messaging": [
        "Core message 1 based on business description",
        "Core message 2 based on services offered",
        "Core message 3 addressing competitive landscape"
    ],
    "campaign_objectives": [
        "Objective 1 relevant to business type",
        "Objective 2 based on competitive analysis",
        "Objective 3 for audience engagement"
    ],
    "recommended_channels": [
        "Channel 1 appropriate for this industry",
        "Channel 2 based on target audience",
        "Channel 3 for competitive advantage"
    ]
}}

Base all recommendations on the provided authentic data only. Do not invent or assume information.
"""
    
    def _create_prompt_generation_request(self, strategy: Dict[str, Any]) -> str:
        """Create request for content prompt generation"""
        return f"""
Based on this marketing strategy, generate specific content creation prompts:

STRATEGY SUMMARY:
- Target Audience: {strategy.get('target_audience', {}).get('primary', 'Not specified')}
- Value Proposition: {strategy.get('value_proposition', 'Not specified')}
- Key Messages: {', '.join(strategy.get('key_messaging', []))}
- Business: {strategy.get('source_business', 'Not specified')}

Generate content prompts in this exact JSON format:
{{
    "image_prompts": [
        {{
            "id": "img_1",
            "title": "Professional Brand Visual",
            "prompt": "Create a professional marketing image for [business name] that emphasizes [specific value prop]. Style: clean, modern, business-focused.",
            "style": "professional",
            "target_platform": "website"
        }},
        {{
            "id": "img_2", 
            "title": "Social Media Graphic",
            "prompt": "Design an engaging social media graphic for [business name] highlighting [key message]. Style: eye-catching, brand-appropriate.",
            "style": "social",
            "target_platform": "instagram"
        }},
        {{
            "id": "img_3",
            "title": "Ad Visual",
            "prompt": "Create advertising visual for [business name] focusing on [competitive advantage]. Style: compelling, conversion-focused.",
            "style": "advertising",
            "target_platform": "facebook"
        }}
    ],
    "video_prompts": [
        {{
            "id": "vid_1",
            "title": "Brand Introduction",
            "prompt": "30-second brand introduction video for [business name] explaining [value proposition] to [target audience]",
            "duration": "30s",
            "style": "professional"
        }},
        {{
            "id": "vid_2",
            "title": "Product Demo",
            "prompt": "15-second demonstration showing [business name]'s key benefits for [target audience]",
            "duration": "15s", 
            "style": "demo"
        }}
    ],
    "text_prompts": [
        {{
            "id": "txt_1",
            "title": "Social Media Post",
            "prompt": "Write engaging social media content for [business name] that highlights [key message] and encourages [target action]",
            "platform": "instagram",
            "tone": "engaging"
        }},
        {{
            "id": "txt_2",
            "title": "Ad Copy", 
            "prompt": "Create compelling ad copy for [business name] that addresses [target audience pain point] and promotes [value proposition]",
            "platform": "facebook",
            "tone": "persuasive"
        }},
        {{
            "id": "txt_3",
            "title": "Email Subject Line",
            "prompt": "Generate attention-grabbing email subject line for [business name] promoting [key offering]",
            "platform": "email",
            "tone": "intriguing"
        }},
        {{
            "id": "txt_4",
            "title": "Website Headline",
            "prompt": "Create compelling website headline for [business name] that immediately communicates [value proposition]",
            "platform": "website", 
            "tone": "professional"
        }},
        {{
            "id": "txt_5",
            "title": "Product Description",
            "prompt": "Write detailed product/service description for [business name] emphasizing [key benefits] for [target audience]",
            "platform": "website",
            "tone": "informative"
        }}
    ]
}}

Replace [placeholders] with specific information from the strategy. Make all prompts specific and actionable.
"""