"""
Payment Blueprint for Dominate Marketing
Handles subscription management and Stripe integration
"""
import os
import logging
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session, flash
from flask_login import login_required, current_user

from services.payment_system import PaymentTier, SubscriptionManager, PaymentNotificationService
from models import db, User, Brand

payment_routes_bp = Blueprint('payment_routes', __name__, url_prefix='/payment')

@payment_routes_bp.route('/pricing')
def pricing():
    """Display pricing plans"""
    return render_template('payment/pricing.html')

@payment_routes_bp.route('/checkout')
@login_required
def checkout():
    """Display checkout page for selected tier"""
    
    tier = request.args.get('tier', 'BASIC').upper()
    brand_id = request.args.get('brand_id')
    
    # Validate tier
    if tier not in PaymentTier.TIERS:
        flash('Invalid subscription tier selected.', 'error')
        return redirect(url_for('payment_routes.pricing'))
    
    tier_config = PaymentTier.TIERS[tier]
    
    # Get selected brand if provided
    selected_brand = None
    if brand_id:
        selected_brand = Brand.query.filter_by(id=brand_id, user_id=current_user.id).first()
    
    # Calculate billing date (today + 1 month)
    billing_date = (datetime.now() + timedelta(days=30)).strftime('%B %d')
    
    return render_template('payment/checkout.html',
                         tier=tier,
                         tier_config=tier_config,
                         selected_brand=selected_brand,
                         billing_date=billing_date)

@payment_routes_bp.route('/create-checkout-session', methods=['POST'])
@login_required
def create_checkout_session():
    """Create Stripe checkout session"""
    
    try:
        data = request.get_json() or {}
        tier = data.get('tier', 'BASIC').upper()
        brand_id = data.get('brand_id')
        
        # Validate tier
        if tier not in PaymentTier.TIERS:
            return jsonify({"error": "Invalid subscription tier", "success": False}), 400
        
        # Create checkout session
        subscription_manager = SubscriptionManager()
        result = subscription_manager.create_checkout_session(
            user_id=current_user.id,
            tier=tier,
            brand_id=brand_id
        )
        
        return jsonify(result)
        
    except Exception as e:
        logging.error(f"Checkout session creation failed: {e}")
        return jsonify({"error": str(e), "success": False}), 500

@payment_routes_bp.route('/success')
@login_required
def payment_success():
    """Handle successful payment"""
    
    session_id = request.args.get('session_id')
    
    if not session_id:
        flash('Invalid payment session.', 'error')
        return redirect(url_for('dashboard.index'))
    
    # Handle successful payment
    subscription_manager = SubscriptionManager()
    result = subscription_manager.handle_successful_payment(session_id)
    
    if result.get('success'):
        flash(f'Welcome to {result.get("tier")} tier! Your subscription is now active.', 'success')
        return render_template('payment/success.html', 
                             tier=result.get('tier'),
                             tier_config=PaymentTier.TIERS.get(result.get('tier')))
    else:
        flash('Payment processing failed. Please contact support.', 'error')
        return redirect(url_for('dashboard.index'))

@payment_routes_bp.route('/cancel')
def payment_cancel():
    """Handle cancelled payment"""
    flash('Payment was cancelled. Your subscription was not activated.', 'warning')
    return redirect(url_for('payment_routes.pricing'))

@payment_routes_bp.route('/manage-subscription')
@login_required
def manage_subscription():
    """Subscription management page"""
    
    # Get current user subscription info
    current_tier = getattr(current_user, 'subscription_tier', 'BASIC')
    tier_config = PaymentTier.TIERS.get(current_tier, PaymentTier.TIERS['BASIC'])
    
    # Check generation usage
    subscription_manager = SubscriptionManager()
    usage_info = subscription_manager.check_generation_limits(current_user.id)
    
    return render_template('payment/manage_subscription.html',
                         current_tier=current_tier,
                         tier_config=tier_config,
                         usage_info=usage_info)

@payment_routes_bp.route('/cancel-subscription', methods=['POST'])
@login_required
def cancel_subscription():
    """Cancel current subscription"""
    
    try:
        subscription_manager = SubscriptionManager()
        result = subscription_manager.cancel_subscription(current_user.id)
        
        if result.get('success'):
            flash('Your subscription has been cancelled and will end at the end of your current billing period.', 'info')
        else:
            flash('Failed to cancel subscription: ' + result.get('error', 'Unknown error'), 'error')
        
        return redirect(url_for('payment_routes.manage_subscription'))
        
    except Exception as e:
        logging.error(f"Subscription cancellation failed: {e}")
        flash('Failed to cancel subscription. Please contact support.', 'error')
        return redirect(url_for('payment_routes.manage_subscription'))

@payment_routes_bp.route('/upgrade')
@login_required
def upgrade_subscription():
    """Show upgrade options"""
    
    current_tier = getattr(current_user, 'subscription_tier', 'BASIC')
    
    # Get tiers above current tier
    tier_order = ['BASIC', 'PLUS', 'PRO', 'ENTERPRISE']
    current_index = tier_order.index(current_tier) if current_tier in tier_order else 0
    available_upgrades = tier_order[current_index + 1:]
    
    upgrade_options = {}
    for tier in available_upgrades:
        upgrade_options[tier] = PaymentTier.TIERS[tier]
    
    return render_template('payment/upgrade.html',
                         current_tier=current_tier,
                         current_config=PaymentTier.TIERS[current_tier],
                         upgrade_options=upgrade_options)

@payment_routes_bp.route('/add-brand')
@login_required
def add_brand_subscription():
    """Add additional brand subscription"""
    
    # Get user's existing brands
    user_brands = Brand.query.filter_by(user_id=current_user.id).all()
    
    return render_template('payment/add_brand.html',
                         additional_brand_price=PaymentTier.ADDITIONAL_BRAND_PRICE,
                         existing_brands=user_brands)

@payment_routes_bp.route('/account-hold', methods=['POST'])
@login_required
def put_account_on_hold():
    """Put account on hold (90 days max, once per year)"""
    
    try:
        # Check if user has already used hold this year
        current_year = datetime.now().year
        last_hold_year = getattr(current_user, 'last_hold_year', None)
        
        if last_hold_year == current_year:
            return jsonify({
                "success": False,
                "error": "You can only put your account on hold once per calendar year."
            }), 400
        
        # Set account on hold
        current_user.account_on_hold = True
        current_user.hold_start_date = datetime.utcnow()
        current_user.hold_end_date = datetime.utcnow() + timedelta(days=90)
        current_user.last_hold_year = current_year
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Account put on hold for 90 days. Billing is paused.",
            "hold_end_date": current_user.hold_end_date.strftime('%Y-%m-%d')
        })
        
    except Exception as e:
        logging.error(f"Account hold failed: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@payment_routes_bp.route('/webhook', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhooks"""
    
    import stripe
    
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')
    endpoint_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError:
        logging.error("Invalid payload in Stripe webhook")
        return "Invalid payload", 400
    except stripe.error.SignatureVerificationError:
        logging.error("Invalid signature in Stripe webhook")
        return "Invalid signature", 400
    
    # Handle the event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        handle_successful_payment(session)
    
    elif event['type'] == 'invoice.payment_failed':
        invoice = event['data']['object']
        handle_payment_failure(invoice)
    
    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        handle_subscription_cancellation(subscription)
    
    return "Webhook received", 200

def handle_successful_payment(session):
    """Process successful payment webhook"""
    
    try:
        subscription_manager = SubscriptionManager()
        result = subscription_manager.handle_successful_payment(session['id'])
        logging.info(f"Payment processed: {result}")
    except Exception as e:
        logging.error(f"Failed to process payment webhook: {e}")

def handle_payment_failure(invoice):
    """Process payment failure webhook"""
    
    try:
        customer_id = invoice['customer']
        user = User.query.filter_by(stripe_customer_id=customer_id).first()
        
        if user:
            # Send payment failure notification
            notification_service = PaymentNotificationService()
            notification_service.send_payment_failure_notice(user)
            
            # Mark account for deletion in 30 days
            user.payment_failed_date = datetime.utcnow()
            user.account_deletion_date = datetime.utcnow() + timedelta(days=30)
            
            db.session.commit()
            
            logging.info(f"Payment failure processed for user {user.id}")
        
    except Exception as e:
        logging.error(f"Failed to process payment failure webhook: {e}")

def handle_subscription_cancellation(subscription):
    """Process subscription cancellation webhook"""
    
    try:
        user = User.query.filter_by(stripe_subscription_id=subscription['id']).first()
        
        if user:
            user.subscription_tier = 'BASIC'
            user.stripe_subscription_id = None
            user.subscription_expires = datetime.utcnow()
            
            db.session.commit()
            
            logging.info(f"Subscription cancelled for user {user.id}")
        
    except Exception as e:
        logging.error(f"Failed to process cancellation webhook: {e}")

# Generation limit checking decorator
def check_generation_limits(f):
    """Decorator to check generation limits before content creation"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({"error": "Authentication required"}), 401
        
        subscription_manager = SubscriptionManager()
        limit_check = subscription_manager.check_generation_limits(current_user.id)
        
        if not limit_check.get('can_generate'):
            return jsonify({
                "error": "Generation limit exceeded",
                "reason": limit_check.get('reason'),
                "reset_date": limit_check.get('reset_date').isoformat() if limit_check.get('reset_date') else None
            }), 429
        
        # Increment generation count
        subscription_manager.increment_generation_count(current_user.id)
        
        return f(*args, **kwargs)
    
    return decorated_function