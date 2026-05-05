"""
Content enhancement service - improves AI-generated content with additional context.
"""
import logging
import os
from openai import OpenAI

logger = logging.getLogger(__name__)


class ContentEnhancementService:
    def __init__(self):
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.model = "gpt-4o-mini"

    def enhance_text(self, content: str, brand_voice: str = "professional", context: str = "") -> str:
        """Enhance text content for better engagement."""
        try:
            prompt = f"""Enhance this marketing content to be more engaging and viral.
Brand voice: {brand_voice}
Additional context: {context}

Original content:
{content}

Return only the enhanced content, no explanations."""
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Content enhancement failed: {e}")
            return content  # Return original if enhancement fails

    def add_cta(self, content: str, goal: str = "engagement") -> str:
        """Add a call-to-action to content."""
        ctas = {
            "engagement": "Drop a comment below and let us know what you think!",
            "sales": "Click the link in bio to get started today!",
            "awareness": "Share this with someone who needs to see it!",
            "leads": "DM us for a free consultation!",
        }
        cta = ctas.get(goal, ctas["engagement"])
        return f"{content}\n\n{cta}"

    def adjust_for_platform(self, content: str, platform: str) -> str:
        """Adjust content length and style for specific social platform."""
        limits = {
            "twitter": 280,
            "instagram": 2200,
            "facebook": 63206,
            "linkedin": 3000,
            "tiktok": 2200,
        }
        limit = limits.get(platform.lower(), 2200)
        if len(content) > limit:
            content = content[:limit - 3] + "..."
        return content
