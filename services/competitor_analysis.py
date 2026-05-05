from datetime import datetime
import requests
from openai import OpenAI
import json
import os
from typing import Dict, List
from services.web_scraper import scrape_business_data

def _get_client():
    """Lazy OpenAI client — avoids import-time credential errors."""
    from openai import OpenAI
    import os
    return OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

client = None  # use _get_client() to get the real client
def analyze_competitors(business_url: str, business_data: Dict, industry: str = None) -> Dict:
    """
    Use AI to identify top 5 competitors and analyze their strategies.
    """
    try:
        # Step 1: Identify competitors using AI
        competitors = identify_competitors(business_data, industry)
        
        # Step 2: Analyze each competitor
        competitor_analysis = []
        for comp in competitors[:5]:  # Top 5 only
            analysis = analyze_single_competitor(comp, business_data)
            if analysis:
                competitor_analysis.append(analysis)
        
        # Step 3: Generate competitive insights
        insights = generate_competitive_insights(business_data, competitor_analysis)
        
        return {
            "competitors": competitor_analysis,
            "insights": insights,
            "analysis_date": str(datetime.utcnow())
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "competitors": [],
            "insights": {}
        }

def identify_competitors(business_data: Dict, industry: str = None) -> List[str]:
    """
    Use OpenAI to identify likely competitors based on business data.
    """
    try:
        business_description = f"""
        Business: {business_data.get('title', '')}
        Description: {business_data.get('description', '')}
        Industry: {industry or 'Unknown'}
        Products/Services: {', '.join(business_data.get('products_services', []))}
        Main Content: {business_data.get('main_text', '')[:1000]}
        """
        
        prompt = f"""Based on this business information, identify 8-10 likely direct competitors. 
        Focus on businesses that offer similar products/services to the same target market.
        
        {business_description}
        
        Return a JSON list of competitor names only. Be specific with company names.
        Example: ["CompanyA", "CompanyB", "CompanyC"]
        
        Focus on real, well-known companies in this space."""
        
        response = _get_client().chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.3
        )
        
        result = json.loads(response.choices[0].message.content)
        return result.get("competitors", [])
        
    except Exception as e:
        print(f"Error identifying competitors: {e}")
        return []

def analyze_single_competitor(competitor_name: str, business_data: Dict) -> Dict:
    """
    Analyze a single competitor's strengths, weaknesses, and strategies.
    """
    try:
        # Use AI to research the competitor
        prompt = f"""
        Research and analyze this competitor: {competitor_name}
        
        Original business context:
        - Products/Services: {', '.join(business_data.get('products_services', []))}
        - Differentiators: {', '.join(business_data.get('differentiators', []))}
        
        Provide analysis in JSON format:
        {{
            "name": "{competitor_name}",
            "description": "brief company description",
            "strengths": ["list of 3-4 key strengths"],
            "weaknesses": ["list of 3-4 potential weaknesses"],
            "marketing_strategies": ["list of their successful marketing approaches"],
            "unique_selling_points": ["what makes them stand out"],
            "target_audience": "their primary target audience",
            "pricing_strategy": "their general pricing approach"
        }}
        """
        
        response = _get_client().chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.4
        )
        
        return json.loads(response.choices[0].message.content)
        
    except Exception as e:
        print(f"Error analyzing competitor {competitor_name}: {e}")
        return None

def generate_competitive_insights(business_data: Dict, competitor_analysis: List[Dict]) -> Dict:
    """
    Generate strategic insights based on competitive analysis.
    """
    try:
        competitors_summary = json.dumps(competitor_analysis, indent=2)
        
        prompt = f"""
        Based on this competitive analysis, generate strategic marketing insights.
        
        Our Business:
        - Products/Services: {', '.join(business_data.get('products_services', []))}
        - Differentiators: {', '.join(business_data.get('differentiators', []))}
        - Description: {business_data.get('description', '')}
        
        Competitor Analysis:
        {competitors_summary}
        
        Provide insights in JSON format:
        {{
            "market_gaps": ["opportunities competitors are missing"],
            "differentiation_opportunities": ["how to stand out from competitors"],
            "messaging_angles": ["unique messaging approaches to try"],
            "target_audience_insights": ["underserved audience segments"],
            "trending_strategies": ["successful strategies competitors are using"],
            "viral_opportunities": ["creative angles that could go viral"],
            "competitive_advantages": ["our strongest advantages over competitors"],
            "recommended_positioning": "recommended market positioning"
        }}
        """
        
        response = _get_client().chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.6
        )
        
        return json.loads(response.choices[0].message.content)
        
    except Exception as e:
        print(f"Error generating competitive insights: {e}")
        return {}

def get_industry_trends(industry: str, business_context: str) -> Dict:
    """
    Get current industry trends and memes relevant to the business.
    """
    try:
        prompt = f"""
        Research current trends, memes, and viral content opportunities for the {industry} industry.
        
        Business context: {business_context}
        
        Provide trends in JSON format:
        {{
            "current_trends": ["list of current industry trends"],
            "viral_content_ideas": ["creative viral content opportunities"],
            "relevant_memes": ["memes or cultural references that could work"],
            "seasonal_opportunities": ["seasonal marketing opportunities"],
            "emerging_technologies": ["new tech trends affecting the industry"],
            "social_media_trends": ["trending formats on social platforms"]
        }}
        """
        
        response = _get_client().chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.7
        )
        
        return json.loads(response.choices[0].message.content)
        
    except Exception as e:
        print(f"Error getting industry trends: {e}")
        return {}

from datetime import datetime