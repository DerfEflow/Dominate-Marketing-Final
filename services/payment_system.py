"""
Payment system stub - delegates to stripe_payment_system.py
This module provides compatibility aliases used by payment.py routes.
"""
from enum import Enum

class PaymentTier(Enum):
    BASIC = "basic"
    PLUS = "plus"
    PRO = "pro"
    ENTERPRISE = "enterprise"

    @property
    def price_monthly(self):
        prices = {
            "basic": 2900,
            "plus": 5900,
            "pro": 9900,
            "enterprise": 19900,
        }
        return prices.get(self.value, 0)

    @property
    def display_name(self):
        return self.value.title()


class SubscriptionManager:
    def __init__(self, user):
        self.user = user

    def get_current_tier(self):
        return self.user.subscription_tier

    def is_active(self):
        return self.user.has_active_subscription()

    def upgrade_to(self, tier):
        """Handled by Stripe webhook in stripe_payment_system.py"""
        pass


class PaymentNotificationService:
    @staticmethod
    def notify_payment_success(user, tier):
        import logging
        logging.info(f"Payment success for {user.email} - tier: {tier}")

    @staticmethod
    def notify_payment_failed(user):
        import logging
        logging.warning(f"Payment failed for {user.email}")
