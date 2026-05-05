"""
AI Processor - Core AI integration for content generation and quality assessment
"""

import os
import json
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import openai
from openai import OpenAI

# the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
# do not change this unless explicitly requested by the user

class AIProcessor:
    """Main AI processor for marketing content generation"""
    
    def __init__(self):
        self.openai_key = os.environ.get('OPENAI_API_KEY')
        if not self.openai_key:
            logging.warning("OPENAI_API_KEY not found - AI processing will be limited")
            self.client = None
        else:
            self.client = OpenAI(api_key=self.openai_key)
    
    def generate_marketing_campaign(self, business_info: Dict, campaign_goal: str, 
                                  target_audience: str, subscription_tier: str) -> Dict:
        """Generate complete marketing campaign based on business data"""
        if not self.client:
            return self._generate_fallback_content(business_info, campaign_goal)
        
        try:
            # Create comprehensive prompt
            system_prompt = """You are an elite marketing strategist with expertise in viral campaigns. 
            Generate high-converting marketing content that captures attention and drives action.
            Always include strong calls-to-action and ensure content aligns with current trends."""
            
            user_prompt = f"""
            Create a comprehensive marketing campaign for this business:
            
            BUSINESS DETAILS:
            - Name: {business_info.get('title', 'Business')}
            - Industry: {business_info.get('industry', 'General')}
            - Description: {business_info.get('description', 'Professional business')}
            - Website: {business_info.get('url', 'Not provided')}
            - Key Services: {', '.join(business_info.get('keywords', [])[:5])}
            
            CAMPAIGN PARAMETERS:
            - Goal: {campaign_goal}
            - Target Audience: {target_audience}
            - Subscription Tier: {subscription_tier}
            
            Generate content appropriate for tier:
            - Basic: Text marketing copy only
            - Plus: Text + image concept 
            - Pro: Text + image + video concept
            - Enterprise: Full campaign suite
            
            Respond in JSON format:
            {{
                "marketing_theme": {{
                    "theme_title": "Campaign theme name",
                    "core_concept": "Central marketing concept",
                    "key_messages": ["message1", "message2", "message3"],
                    "visual_style": "Description of visual approach",
                    "tone_of_voice": "Marketing tone description"
                }},
                "ad_text": "Complete marketing copy with strong call-to-action",
                "image_prompt": "Detailed image generation prompt (if Plus/Pro/Enterprise)",
                "video_prompt": {{
                    "concept": "Video concept description",
                    "script": "Video script",
                    "visual_elements": ["element1", "element2"],
                    "duration": 30,
                    "aspect_ratio": "9:16"
                }},
                "social_posts": [
                    {{"platform": "Instagram", "content": "Post content", "hashtags": ["#tag1", "#tag2"]}},
                    {{"platform": "LinkedIn", "content": "Professional post content"}}
                ],
                "success_metrics": ["metric1", "metric2", "metric3"]
            }}
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.7,
                max_tokens=2000
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # Filter content based on subscription tier
            filtered_result = self._filter_content_by_tier(result, subscription_tier)
            filtered_result['generated_at'] = datetime.now().isoformat()
            filtered_result['ai_model'] = 'gpt-4o'
            
            return filtered_result
            
        except Exception as e:
            logging.error(f"AI content generation failed: {e}")
            return self._generate_fallback_content(business_info, campaign_goal)
    
    def assess_content_quality(self, content: Dict, business_info: Dict) -> Dict:
        """Assess quality of generated marketing content"""
        if not self.client:
            return self._basic_quality_check(content)
        
        try:
            assessment_prompt = f"""
            Evaluate this marketing content for quality and effectiveness:
            
            BUSINESS: {business_info.get('title', 'Unknown')}
            CONTENT: {json.dumps(content, indent=2)}
            
            Rate each aspect from 0-100:
            1. Coherence and clarity
            2. Marketing effectiveness 
            3. Brand appropriateness
            4. Call-to-action strength
            5. Overall quality
            
            Check for:
            - Grammar/spelling errors
            - Inappropriate content
            - Missing elements
            - Improvement opportunities
            
            Respond in JSON:
            {{
                "overall_score": 85,
                "coherence_score": 90,
                "effectiveness_score": 80,
                "appropriateness_score": 95,
                "cta_strength_score": 75,
                "passes_quality_check": true,
                "issues_found": ["Minor issue"],
                "recommendations": ["Suggestion"],
                "approved_for_delivery": true
            }}
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": assessment_prompt}],
                response_format={"type": "json_object"},
                temperature=0.1,
                max_tokens=800
            )
            
            assessment = json.loads(response.choices[0].message.content)
            assessment['assessed_at'] = datetime.now().isoformat()
            
            return assessment
            
        except Exception as e:
            logging.error(f"Content assessment failed: {e}")
            return self._basic_quality_check(content)
    
    def process_user_revision(self, original_content: str, user_feedback: str, 
                            business_info: Dict, content_type: str) -> str:
        """Process user revision request and generate improved content"""
        if not self.client:
            return f"Revised: {original_content} (Note: {user_feedback})"
        
        try:
            revision_prompt = f"""
            Revise this marketing content based on user feedback:
            
            ORIGINAL CONTENT:
            {original_content}
            
            USER FEEDBACK:
            {user_feedback}
            
            BUSINESS: {business_info.get('title', 'Business')}
            CONTENT TYPE: {content_type}
            
            Generate improved content that addresses the feedback while maintaining:
            - Professional quality
            - Strong marketing effectiveness
            - Brand consistency
            - Clear call-to-action
            
            Return only the revised content, no explanations.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": revision_prompt}],
                temperature=0.5,
                max_tokens=1000
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logging.error(f"Content revision failed: {e}")
            return f"Revised: {original_content}"
    
    def _filter_content_by_tier(self, content: Dict, tier: str) -> Dict:
        """Filter generated content based on subscription tier"""
        result = {"ad_text": content.get("ad_text", "")}
        
        if tier in ['plus', 'pro', 'enterprise']:
            result["image_prompt"] = content.get("image_prompt", "")
            result["marketing_theme"] = content.get("marketing_theme", {})
        
        if tier in ['pro', 'enterprise']:
            result["video_prompt"] = content.get("video_prompt", {})
        
        if tier == 'enterprise':
            result["social_posts"] = content.get("social_posts", [])
            result["success_metrics"] = content.get("success_metrics", [])
        
        return result
    
    def _generate_fallback_content(self, business_info: Dict, campaign_goal: str) -> Dict:
        """Generate basic fallback content when AI is unavailable"""
        business_name = business_info.get('title', 'Your Business')
        
        return {
            "ad_text": f"Transform your business with {business_name}! "
                      f"Our proven solutions help you achieve {campaign_goal.lower()}. "
                      f"Join thousands of satisfied customers today. "
                      f"Contact us now for your free consultation!",
            "marketing_theme": {
                "theme_title": f"{business_name} Success Campaign",
                "core_concept": f"Professional {campaign_goal.lower()} solutions",
                "key_messages": ["Proven results", "Expert service", "Customer focused"],
                "visual_style": "Professional and trustworthy",
                "tone_of_voice": "Confident and approachable"
            },
            "generated_at": datetime.now().isoformat(),
            "ai_model": "fallback",
            "note": "Generated with basic template - upgrade for AI-powered content"
        }
    
    def _basic_quality_check(self, content: Dict) -> Dict:
        """Basic quality check when AI assessment is unavailable"""
        ad_text = content.get('ad_text', '')
        word_count = len(ad_text.split()) if ad_text else 0
        has_cta = any(word in ad_text.lower() for word in ['call', 'contact', 'buy', 'get', 'join'])
        
        score = 70 if word_count > 20 and has_cta else 40
        
        return {
            "overall_score": score,
            "passes_quality_check": score >= 60,
            "issues_found": [] if score >= 60 else ["Content too short or missing call-to-action"],
            "approved_for_delivery": score >= 60,
            "assessed_at": datetime.now().isoformat(),
            "note": "Basic assessment - upgrade for AI quality control"
        }


class DataExporter:
    """Handle data export functionality"""
    
    @staticmethod
    def export_campaign_data(campaign: Dict, format: str = 'json') -> str:
        """Export campaign data in specified format"""
        if format.lower() == 'json':
            return json.dumps(campaign, indent=2)
        
        elif format.lower() == 'csv':
            # Simple CSV export for basic data
            # Escape quotes for CSV
            ad_text_escaped = campaign.get('ad_text', '').replace('"', '""')
            lines = [
                "Field,Value",
                f"Title,\"{campaign.get('title', '')}\"",
                f"Goal,\"{campaign.get('campaign_goal', '')}\"",
                f"Target Audience,\"{campaign.get('target_audience', '')}\"",
                f"Business URL,\"{campaign.get('business_url', '')}\"",
                f"Created,\"{campaign.get('created_at', '')}\"",
                f"Status,\"{campaign.get('status', '')}\"",
                f"Ad Text,\"{ad_text_escaped}\"",
            ]
            return '\n'.join(lines)
        
        elif format.lower() == 'txt':
            lines = [
                f"Campaign: {campaign.get('title', 'Untitled')}",
                f"Goal: {campaign.get('campaign_goal', 'Not specified')}",
                f"Target Audience: {campaign.get('target_audience', 'General')}",
                f"Created: {campaign.get('created_at', 'Unknown')}",
                "",
                "Marketing Copy:",
                campaign.get('ad_text', 'No content generated'),
                "",
                f"Business URL: {campaign.get('business_url', 'Not provided')}"
            ]
            return '\n'.join(lines)
        
        else:
            return json.dumps(campaign, indent=2)  # Default to JSON


# Export main classes
__all__ = ['AIProcessor', 'DataExporter']