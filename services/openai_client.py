import os
import json
import logging
from typing import Dict
from openai import OpenAI

# Configure logging
logger = logging.getLogger(__name__)

def summarize_url(url: str, brand_voice: str) -> Dict:
    """
    Summarize business information from a URL using advanced AI language models.
    
    Args:
        url (str): The business URL to analyze
        brand_voice (str): The desired brand voice for alignment
        
    Returns:
        dict: Summary with keys: product, audience, value_props, proof_points, tone_guess
              or {"error": "message"} on failure
    """
    try:
        # Get API key from environment
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            logger.error("OPENAI_API_KEY not found in environment variables")
            return {"error": "AI API key not configured. Please add OPENAI_API_KEY to Replit Secrets."}
        
        # Set API key in environment for AI client
        os.environ['OPENAI_API_KEY'] = api_key
        
        # Initialize AI client (will read from environment)
        client = OpenAI()
        
        # Construct prompt
        prompt = f"""Return compact JSON only with these keys:
product, audience, value_props, proof_points, tone_guess.
Source URL: {url}
Align tone with: {brand_voice}.
If the page is light on details, infer typical details for the niche and mark them as "inferred"."""
        
        # Make API call
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user", 
                "content": prompt
            }],
            response_format={"type": "json_object"},
            temperature=0.3,
            max_tokens=500
        )
        
        # Parse response
        content = response.choices[0].message.content
        if not content:
            return {"error": "Empty response from AI API"}
        summary_data = json.loads(content)
        
        logger.info(f"Successfully summarized URL: {url}")
        return summary_data
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse AI response as JSON: {str(e)}")
        return {"error": f"Failed to parse AI response: {str(e)}"}
    
    except Exception as e:
        logger.error(f"Error summarizing URL {url}: {str(e)}")
        return {"error": f"Failed to generate summary: {str(e)}"}