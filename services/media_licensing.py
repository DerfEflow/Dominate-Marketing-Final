"""
Media licensing service - generates usage licenses for AI-generated content.
"""
import uuid
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class MediaLicensingGenerator:
    def generate_license(self, user_id: str, campaign_id: str, content_type: str) -> dict:
        """Generate a usage license for a piece of AI content."""
        license_id = str(uuid.uuid4())
        return {
            "license_id": license_id,
            "user_id": user_id,
            "campaign_id": campaign_id,
            "content_type": content_type,
            "issued_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(days=365)).isoformat(),
            "license_type": "commercial",
            "restrictions": "AI-generated content. User retains rights to output.",
            "terms": "Content generated using Dominate Marketing AI tools may be used commercially.",
        }

    def verify_license(self, license_id: str) -> bool:
        """Verify a license is valid (extend with DB persistence as needed)."""
        return bool(license_id) and len(license_id) == 36

    def download_license_pdf(self, license_data: dict) -> bytes:
        """Generate a simple text-based license document."""
        content = f"""
DOMINATE MARKETING — CONTENT LICENSE
=====================================
License ID: {license_data.get('license_id')}
Issued: {license_data.get('issued_at')}
Expires: {license_data.get('expires_at')}
Type: {license_data.get('license_type', 'commercial').title()}

{license_data.get('terms', '')}
""".strip()
        return content.encode("utf-8")
