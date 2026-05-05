from openai import OpenAI
import json
import os
from typing import Dict, List, Optional
from datetime import datetime

def _get_client():
    """Lazy OpenAI client — avoids import-time credential errors."""
    from openai import OpenAI
    import os
    return OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

client = None  # use _get_client() to get the real client
def generate_marketing_theme(business_data: Dict, competitor_insights: Dict, industry_trends: Dict, user_document: str = None) -> Dict:
    """
    Generate a comprehensive marketing theme that's creative, viral-worthy, and effective.
    """
    try:
        # Compile all context
        context = f"""
        BUSINESS PROFILE:
        - Company: {business_data.get('title', '')}
        - Description: {business_data.get('description', '')}
        - Products/Services: {', '.join(business_data.get('products_services', []))}
        - Differentiators: {', '.join(business_data.get('differentiators', []))}
        - Keywords: {', '.join(business_data.get('keywords', [])[:10])}
        
        COMPETITIVE LANDSCAPE:
        - Market Gaps: {', '.join(competitor_insights.get('market_gaps', []))}
        - Differentiation Opportunities: {', '.join(competitor_insights.get('differentiation_opportunities', []))}
        - Viral Opportunities: {', '.join(competitor_insights.get('viral_opportunities', []))}
        
        INDUSTRY TRENDS:
        - Current Trends: {', '.join(industry_trends.get('current_trends', []))}
        - Viral Content Ideas: {', '.join(industry_trends.get('viral_content_ideas', []))}
        - Relevant Memes: {', '.join(industry_trends.get('relevant_memes', []))}
        
        USER CONTEXT: {user_document or 'No additional context provided'}
        """
        
        prompt = f"""You are a world-class creative marketing strategist. Create an innovative, viral-worthy marketing theme that will make this business stand out dramatically from competitors.

        {context}

        Create a marketing theme that is:
        1. HIGHLY CREATIVE - Something the client wouldn't think of themselves
        2. VIRAL POTENTIAL - Designed to capture attention and be shared
        3. AUTHENTIC - True to the brand while being memorable
        4. TREND-AWARE - Incorporates current trends and cultural moments
        5. DIFFERENTIATED - Clearly sets them apart from competitors

        Return in JSON format:
        {{
            "theme_title": "Catchy theme name",
            "core_concept": "The main creative idea in 2-3 sentences",
            "key_messages": ["3-4 key messages that support this theme"],
            "target_emotions": ["emotions this theme should evoke"],
            "visual_style": "Description of visual aesthetic and style",
            "tone_of_voice": "Brand voice for this campaign",
            "viral_hooks": ["Specific elements designed to go viral"],
            "cultural_relevance": "How this taps into current culture/trends",
            "differentiation_angle": "How this sets them apart from competitors",
            "call_to_action_style": "Type of CTA that fits this theme",
            "content_pillars": ["3-4 types of content to create around this theme"],
            "success_metrics": ["What success looks like for this theme"]
        }}
        """
        
        response = _get_client().chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.8,
            max_tokens=1200
        )
        
        return json.loads(response.choices[0].message.content)
        
    except Exception as e:
        return {"error": str(e)}

def generate_ad_content(marketing_theme: Dict, business_data: Dict, ad_format: str = "social_video") -> Dict:
    """
    Generate creative ad content (text, image prompt, video prompt) based on marketing theme.
    """
    try:
        theme_context = json.dumps(marketing_theme, indent=2)
        
        prompt = f"""Create highly creative ad content based on this marketing theme.

        MARKETING THEME:
        {theme_context}
        
        BUSINESS INFO:
        - Company: {business_data.get('title', '')}
        - Services: {', '.join(business_data.get('products_services', []))}
        - Website: {business_data.get('url', '')}
        
        Create content for {ad_format} that is:
        - ATTENTION-GRABBING from the first second
        - EMOTIONALLY ENGAGING
        - AUTHENTIC to the brand
        - OPTIMIZED for social sharing
        - INCLUDES a compelling CTA
        
        Return in JSON format:
        {{
            "ad_text": "Complete ad copy (engaging hook + key message + strong CTA)",
            "image_prompt": "Detailed DALL-E prompt for campaign image (specific, visual, brand-aligned)",
            "video_concept": "Creative video concept description",
            "veo_prompt": {{
                "main_prompt": "Primary video generation prompt for Veo 3",
                "visual_style": "Specific visual style instructions",
                "pacing": "Video pacing and timing details",
                "key_scenes": ["List of 3-5 key scenes/shots"],
                "audio_notes": "Background music and sound effect suggestions",
                "text_overlays": ["Any text that should appear on screen"],
                "call_to_action": "How the CTA should be presented visually"
            }},
            "hashtags": ["Relevant hashtags for social media"],
            "best_platforms": ["Which social platforms this works best on"],
            "posting_recommendations": {{
                "best_times": ["Optimal posting times"],
                "frequency": "Recommended posting frequency",
                "variations": "How to create variations of this content"
            }}
        }}
        """
        
        response = _get_client().chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.7,
            max_tokens=1500
        )
        
        return json.loads(response.choices[0].message.content)
        
    except Exception as e:
        return {"error": str(e)}

def create_image_prompt(marketing_theme: Dict, business_data: Dict) -> str:
    """
    Create a detailed image generation prompt optimized for DALL-E.
    """
    try:
        prompt = f"""Create a detailed image generation prompt for a marketing campaign.

        Marketing Theme: {marketing_theme.get('core_concept', '')}
        Visual Style: {marketing_theme.get('visual_style', '')}
        Business: {business_data.get('title', '')}
        Services: {', '.join(business_data.get('products_services', []))}
        
        Create a DALL-E prompt that is:
        - Highly specific and detailed
        - Visually striking and professional
        - Aligned with the marketing theme
        - Optimized for social media use
        - Brand-appropriate yet creative
        
        Return just the image prompt, nothing else.
        """
        
        response = _get_client().chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6,
            max_tokens=200
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        return f"Professional marketing image for {business_data.get('title', 'business')}, {marketing_theme.get('visual_style', 'modern and clean style')}"

def create_veo_prompt(marketing_theme: Dict, business_data: Dict, video_length: int = 30) -> Dict:
    """
    Create a comprehensive Veo 3 JSON prompt for video generation.
    """
    try:
        theme_json = json.dumps(marketing_theme, indent=2)
        
        prompt = f"""Create a detailed Veo 3 video generation prompt.

        MARKETING THEME:
        {theme_json}
        
        BUSINESS:
        - Company: {business_data.get('title', '')}
        - Services: {', '.join(business_data.get('products_services', []))}
        
        Create a {video_length}-second video prompt that:
        - Implements the marketing theme creatively
        - Has strong viral potential
        - Is visually engaging throughout
        - Includes clear branding moments
        - Ends with a compelling CTA
        
        Return in JSON format exactly as Veo 3 expects:
        {{
            "prompt": "Primary video description (detailed, creative, specific)",
            "style": "Visual style description",
            "duration": {video_length},
            "aspect_ratio": "9:16",
            "camera_movements": ["List of camera movements/shots"],
            "visual_elements": ["Key visual elements to include"],
            "pacing": "How the video should be paced",
            "mood": "Overall mood and energy level",
            "color_palette": "Suggested color scheme",
            "text_overlays": ["Any text that should appear"],
            "audio_cues": "Background music/sound suggestions",
            "call_to_action": "How to present the final CTA"
        }}
        """
        
        response = _get_client().chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.7,
            max_tokens=800
        )
        
        return json.loads(response.choices[0].message.content)
        
    except Exception as e:
        return {
            "prompt": f"Create a {video_length}-second marketing video for {business_data.get('title', 'business')}",
            "style": marketing_theme.get('visual_style', 'modern and professional'),
            "duration": video_length,
            "aspect_ratio": "9:16",
            "error": str(e)
        }

def enhance_with_trends(base_content: Dict, industry_trends: Dict) -> Dict:
    """
    Enhance ad content with current trends and viral elements.
    """
    try:
        content_json = json.dumps(base_content, indent=2)
        trends_json = json.dumps(industry_trends, indent=2)
        
        prompt = f"""Enhance this ad content with current trends and viral elements.

        CURRENT CONTENT:
        {content_json}
        
        INDUSTRY TRENDS:
        {trends_json}
        
        Add viral elements like:
        - Current meme references (when appropriate)
        - Trending audio/music suggestions
        - Popular format adaptations
        - Cultural moment tie-ins
        - Social media trend integration
        
        Return the enhanced content in the same JSON structure, but with trend-enhanced versions.
        """
        
        response = _get_client().chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.8,
            max_tokens=1000
        )
        
        return json.loads(response.choices[0].message.content)
        
    except Exception as e:
        return base_content  # Return original if enhancement fails