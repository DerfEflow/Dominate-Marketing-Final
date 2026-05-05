"""
Stripe Payment System - Complete subscription management with multiple payment methods
Handles recurring billing, Google Pay, Apple Pay, and card payments
"""

import stripe
import os
import logging
from flask import Blueprint, request, jsonify, redirect, url_for, render_template, flash, session
from flask_login import login_required, current_user
from models import User, db, SubscriptionTier
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Initialize Stripe
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY')

# Get domain for URLs
YOUR_DOMAIN = os.environ.get('REPLIT_DEV_DOMAIN') if os.environ.get('REPLIT_DEPLOYMENT') else os.environ.get('REPLIT_DOMAINS', 'localhost:5000').split(',')[0]

payment_bp = Blueprint('payments', __name__, url_prefix='/payments')

# Subscription tier pricing (monthly in USD cents)
SUBSCRIPTION_PRICING = {
    'basic': {
        'price_id': 'price_basic_monthly',  # Replace with actual Stripe Price IDs
        'amount': 2900,  # $29/month
        'name': 'Basic Plan',
        'features': ['Text content generation', 'Basic viral trends', '50 campaigns/month']
    },
    'plus': {
        'price_id': 'price_plus_monthly',
        'amount': 4900,  # $49/month
        'name': 'Plus Plan', 
        'features': ['Text + Image content', 'Advanced viral tools', '150 campaigns/month', 'Social scheduling']
    },
    'pro': {
        'price_id': 'price_pro_monthly',
        'amount': 9900,  # $99/month
        'name': 'Pro Plan',
        'features': ['Text + Image + Video', 'Premium AI models', 'Unlimited campaigns', 'Priority support']
    },
    'enterprise': {
        'price_id': 'price_enterprise_monthly',
        'amount': 19900,  # $199/month
        'name': 'Enterprise Plan',
        'features': ['All Pro features', 'Custom integrations', 'Dedicated support', 'White-label options']
    }
}

class StripePaymentProcessor:
    """Handles all Stripe payment operations"""
    
    def __init__(self):
        self.stripe = stripe
        
    def create_checkout_session(self, tier: str, user_id: int, success_url: str, cancel_url: str, coupon_code: Optional[str] = None) -> Dict[str, Any]:
        """Create Stripe Checkout session with multiple payment methods and coupon support"""
        try:
            if tier not in SUBSCRIPTION_PRICING:
                raise ValueError(f"Invalid subscription tier: {tier}")
            
            pricing = SUBSCRIPTION_PRICING[tier]
            
            # Handle coupon codes
            trial_period_days = None
            discount_coupon = None
            
            if coupon_code:
                if coupon_code == "SAINTSDOMINION":
                    # 24-hour free trial before charging
                    trial_period_days = 1
                elif coupon_code == "SAINTSDOMINIONSTEWARD":
                    # This will be handled separately - lifetime access
                    # For now, we'll create a 100% discount coupon
                    try:
                        discount_coupon = stripe.Coupon.create(
                            percent_off=100,
                            duration='forever',
                            id=f'lifetime_{user_id}_{tier}',
                            max_redemptions=1,
                        )
                    except stripe.error.InvalidRequestError:
                        # Coupon might already exist, try to retrieve it
                        try:
                            discount_coupon = stripe.Coupon.retrieve(f'lifetime_{user_id}_{tier}')
                        except:
                            pass
            
            # Build checkout session parameters
            checkout_params = {
                'payment_method_types': ['card', 'google_pay', 'apple_pay', 'link'],
                'line_items': [{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': pricing['name'],
                            'description': f"Dominate Marketing {pricing['name']} - {', '.join(pricing['features'][:2])}"
                        },
                        'unit_amount': pricing['amount'],
                        'recurring': {'interval': 'month'}
                    },
                    'quantity': 1,
                }],
                'mode': 'subscription',
                'success_url': success_url,
                'cancel_url': cancel_url,
                'client_reference_id': str(user_id),
                'metadata': {
                    'user_id': user_id,
                    'subscription_tier': tier,
                    'coupon_code': coupon_code or '',
                    'platform': 'dominate_marketing'
                },
                'subscription_data': {
                    'metadata': {
                        'user_id': user_id,
                        'tier': tier,
                        'coupon_code': coupon_code or ''
                    }
                },
                'automatic_tax': {'enabled': True},
                'billing_address_collection': 'auto'
            }
            
            # Add trial period if applicable
            if trial_period_days:
                checkout_params['subscription_data']['trial_period_days'] = trial_period_days
                
            # Add discount coupon if applicable
            if discount_coupon:
                checkout_params['discounts'] = [{'coupon': discount_coupon.id}]
            
            # Create checkout session
            checkout_session = self.stripe.checkout.Session.create(**checkout_params)
            
            return {
                'success': True,
                'checkout_url': checkout_session.url,
                'session_id': checkout_session.id
            }
            
        except Exception as e:
            logger.error(f"Error creating checkout session: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def handle_successful_payment(self, session_id: str) -> Dict[str, Any]:
        """Process successful payment and update user subscription"""
        try:
            # Retrieve the checkout session
            session = self.stripe.checkout.Session.retrieve(session_id)
            
            if session.payment_status == 'paid':
                user_id = int(session.metadata.get('user_id'))
                tier = session.metadata.get('subscription_tier')
                coupon_code = session.metadata.get('coupon_code', '')
                
                # Update user subscription
                user = User.query.get(user_id)
                if user:
                    # Handle coupon-specific logic
                    if coupon_code == "SAINTSDOMINION":
                        # 24-hour trial - set trial expiry
                        user.trial_expires = datetime.utcnow() + timedelta(hours=24)
                        user.coupon_used = coupon_code
                    elif coupon_code == "SAINTSDOMINIONSTEWARD":
                        # Lifetime access - set to Enterprise tier forever
                        user.lifetime_access = True
                        user.subscription_tier = SubscriptionTier.ENTERPRISE
                        user.coupon_used = coupon_code
                    else:
                        # Regular subscription
                        user.subscription_tier = SubscriptionTier(tier)
                    
                    user.stripe_customer_id = session.customer
                    if hasattr(session, 'subscription') and session.subscription:
                        user.stripe_subscription_id = session.subscription
                    user.subscription_expires = datetime.utcnow() + timedelta(days=30)
                    
                    db.session.commit()
                    
                    logger.info(f"User {user_id} successfully subscribed to {tier} plan")
                    
                    return {
                        'success': True,
                        'user_id': user_id,
                        'tier': tier,
                        'subscription_id': session.subscription
                    }
            
            return {'success': False, 'error': 'Payment not completed'}
            
        except Exception as e:
            logger.error(f"Error processing successful payment: {e}")
            return {'success': False, 'error': str(e)}
    
    def cancel_subscription(self, user_id: int) -> Dict[str, Any]:
        """Cancel user subscription"""
        try:
            user = User.query.get(user_id)
            if not user or not user.stripe_subscription_id:
                return {'success': False, 'error': 'No active subscription found'}
            
            # Cancel at period end to maintain access until billing cycle ends
            subscription = self.stripe.Subscription.modify(
                user.stripe_subscription_id,
                cancel_at_period_end=True
            )
            
            user.subscription_status = 'cancelled'
            db.session.commit()
            
            return {
                'success': True,
                'cancelled_at': subscription.canceled_at,
                'current_period_end': subscription.current_period_end
            }
            
        except Exception as e:
            logger.error(f"Error cancelling subscription: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_subscription_details(self, user_id: int) -> Dict[str, Any]:
        """Get current subscription details"""
        try:
            user = User.query.get(user_id)
            if not user or not user.stripe_subscription_id:
                return {'success': False, 'error': 'No subscription found'}
            
            subscription = self.stripe.Subscription.retrieve(user.stripe_subscription_id)
            
            return {
                'success': True,
                'status': subscription.status,
                'current_period_end': subscription.current_period_end,
                'cancel_at_period_end': subscription.cancel_at_period_end,
                'amount': subscription.items.data[0].price.unit_amount,
                'currency': subscription.items.data[0].price.currency
            }
            
        except Exception as e:
            logger.error(f"Error getting subscription details: {e}")
            return {'success': False, 'error': str(e)}

# Initialize payment processor
payment_processor = StripePaymentProcessor()

@payment_bp.route('/create-checkout-session', methods=['POST'])
@login_required
def create_checkout_session():
    """Create Stripe checkout session for subscription"""
    try:
        data = request.get_json()
        tier = data.get('tier')
        coupon_code = data.get('coupon_code', '').strip().upper()
        
        if not tier or tier not in SUBSCRIPTION_PRICING:
            return jsonify({'success': False, 'error': 'Invalid subscription tier'}), 400
        
        # Validate coupon codes
        valid_coupons = ["SAINTSDOMINION", "SAINTSDOMINIONSTEWARD"]
        if coupon_code and coupon_code not in valid_coupons:
            return jsonify({'success': False, 'error': 'Invalid coupon code'}), 400
        
        # Create success and cancel URLs
        success_url = f"https://{YOUR_DOMAIN}/payments/success?session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = f"https://{YOUR_DOMAIN}/payments/cancel"
        
        # Create checkout session
        result = payment_processor.create_checkout_session(
            tier=tier,
            user_id=current_user.id,
            success_url=success_url,
            cancel_url=cancel_url,
            coupon_code=coupon_code if coupon_code else None
        )
        
        if result['success']:
            return jsonify({
                'success': True,
                'checkout_url': result['checkout_url']
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500
            
    except Exception as e:
        logger.error(f"Error in create_checkout_session: {e}")
        return jsonify({'success': False, 'error': 'Payment processing error'}), 500

@payment_bp.route('/success')
@login_required
def payment_success():
    """Handle successful payment"""
    session_id = request.args.get('session_id')
    
    if not session_id:
        flash('Invalid payment session', 'error')
        return redirect(url_for('auth.pricing'))
    
    # Process the successful payment
    result = payment_processor.handle_successful_payment(session_id)
    
    if result['success']:
        flash(f'Successfully subscribed to {result["tier"].title()} plan!', 'success')
        return render_template('payments/success.html', 
                             tier=result['tier'], 
                             subscription_id=result['subscription_id'])
    else:
        flash('Payment processing error. Please contact support.', 'error')
        return redirect(url_for('auth.pricing'))

@payment_bp.route('/cancel')
def payment_cancel():
    """Handle cancelled payment"""
    return render_template('payments/cancel.html')

@payment_bp.route('/manage')
@login_required
def manage_subscription():
    """Subscription management page"""
    details = payment_processor.get_subscription_details(current_user.id)
    return render_template('payments/manage.html', 
                         subscription_details=details,
                         current_tier=current_user.subscription_tier)

@payment_bp.route('/cancel-subscription', methods=['POST'])
@login_required
def cancel_subscription():
    """Cancel current subscription"""
    result = payment_processor.cancel_subscription(current_user.id)
    
    if result['success']:
        flash('Subscription cancelled. Access will continue until the end of your billing period.', 'info')
    else:
        flash('Error cancelling subscription. Please contact support.', 'error')
    
    return redirect(url_for('payments.manage_subscription'))

@payment_bp.route('/webhook', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhooks for subscription events"""
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')
    endpoint_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')
    
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except ValueError:
        logger.error("Invalid payload in webhook")
        return '', 400
    except stripe.error.SignatureVerificationError:
        logger.error("Invalid signature in webhook")
        return '', 400
    
    # Handle the event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        payment_processor.handle_successful_payment(session['id'])
        
    elif event['type'] == 'invoice.payment_succeeded':
        invoice = event['data']['object']
        # Handle successful recurring payment
        subscription_id = invoice['subscription']
        logger.info(f"Recurring payment succeeded for subscription {subscription_id}")
        
    elif event['type'] == 'invoice.payment_failed':
        invoice = event['data']['object']
        # Handle failed payment
        subscription_id = invoice['subscription']
        logger.warning(f"Payment failed for subscription {subscription_id}")
        
    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        # Handle subscription cancellation
        logger.info(f"Subscription {subscription['id']} was deleted")
    
    return '', 200

# Utility functions for templates
@payment_bp.context_processor
def inject_stripe_key():
    """Inject Stripe publishable key into templates"""
    return dict(stripe_publishable_key=STRIPE_PUBLISHABLE_KEY)

@payment_bp.context_processor
def inject_pricing():
    """Inject pricing information into templates"""
    return dict(subscription_pricing=SUBSCRIPTION_PRICING)