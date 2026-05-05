"""
Admin notification service - sends internal alerts for user events.
"""
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)

ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "fredwolfe@gmail.com")


class AdminNotificationService:
    def __init__(self):
        self.admin_email = ADMIN_EMAIL

    def notify_new_signup(self, user_email: str, tier: str):
        logger.info(f"[ADMIN ALERT] New signup: {user_email} on {tier} tier at {datetime.utcnow()}")

    def notify_payment_received(self, user_email: str, amount: int, tier: str):
        logger.info(f"[ADMIN ALERT] Payment received: {user_email} - ${amount/100:.2f} for {tier}")

    def notify_payment_failed(self, user_email: str):
        logger.warning(f"[ADMIN ALERT] Payment failed: {user_email}")

    def notify_campaign_generated(self, user_email: str, campaign_id: str):
        logger.info(f"[ADMIN ALERT] Campaign generated: {campaign_id} for {user_email}")

    def notify_error(self, error_type: str, details: str):
        logger.error(f"[ADMIN ALERT] System error - {error_type}: {details}")

    def send_message_to_user(self, user_email: str, subject: str, body: str):
        """Placeholder for email sending - integrate SendGrid/SES here."""
        logger.info(f"[ADMIN MESSAGE] To: {user_email} | Subject: {subject}")
        # TODO: integrate email provider (SendGrid, AWS SES, etc.)
        return False

def notify_quality_failure(campaign_id: str, content_type: str, score: float, details: str = ""):
    """Module-level helper for quality failure notifications."""
    logger.warning(f"[QUALITY FAIL] Campaign {campaign_id} | {content_type} scored {score:.2f} | {details}")

def notify_quality_pass(campaign_id: str, content_type: str, score: float):
    """Module-level helper for quality pass notifications."""
    logger.info(f"[QUALITY PASS] Campaign {campaign_id} | {content_type} scored {score:.2f}")
