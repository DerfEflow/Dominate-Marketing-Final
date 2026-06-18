"""
Authentication blueprint for Dominate Marketing platform
Handles Google OAuth, demo login, and user management
"""

import json
import os
import requests
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from urllib.parse import urlparse
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from models import db, User, SubscriptionTier

# Google OAuth configuration
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_OAUTH_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET')
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

# OAuth callback URL — set OAUTH_CALLBACK_URL env var in Railway to your live domain.
# Falls back to the custom domain so existing Google Cloud Console config still works.
CUSTOM_DOMAIN = "dominatemarketing.ninja"
REPLIT_DEV_DOMAIN = os.environ.get('REPLIT_DEV_DOMAIN', 'localhost:5000')
OAUTH_CALLBACK_URL = os.environ.get(
    'OAUTH_CALLBACK_URL',
    f"https://{CUSTOM_DOMAIN}/auth/google_login/callback"
)

print(f"[AUTH] OAuth callback URL: {OAUTH_CALLBACK_URL}")

auth = Blueprint('auth', __name__)

@auth.route('/signup')
def signup():
    """Signup flow - redirects to pricing to choose plan first"""
    return redirect(url_for('auth.pricing'))

@auth.route('/login')
def login():
    """Login page for existing users"""
    return render_template('auth/login.html')

@auth.route('/login', methods=['POST'])
def login_post():
    """Handle login by email OR username + password.

    The form field is historically named "email", but admin-provisioned
    salespeople sign in with a username (email is optional for them). So we
    accept the value as either an email or a username.
    """
    identifier = (request.form.get('email') or '').strip()
    password = request.form.get('password')
    remember = request.form.get('remember')

    if not identifier or not password:
        flash('Please enter both your email/username and password.', 'error')
        return render_template('auth/login.html')

    # Match on email first, then fall back to username.
    user = User.query.filter_by(email=identifier).first() \
        or User.query.filter_by(username=identifier).first()

    if not user or not user.password_hash or not check_password_hash(user.password_hash, password):
        flash('Invalid email/username or password.', 'error')
        return render_template('auth/login.html')

    # Deactivated accounts cannot log in. An admin deactivates a salesperson by
    # setting account_active=False (admin.py) — this preserves their data but
    # must block sign-in. Only an explicit False blocks; None/True (the column
    # default and any legacy rows) stay allowed so no current user is locked out.
    if user.account_active is False:
        flash('Your account has been deactivated. Please contact your administrator.', 'error')
        return render_template('auth/login.html')

    login_user(user, remember=bool(remember))
    user.last_login = datetime.utcnow()
    db.session.commit()

    # Redirect to dashboard or next page — validate to prevent open redirect
    next_page = request.args.get('next')
    if next_page:
        parsed = urlparse(next_page)
        if parsed.scheme or parsed.netloc:
            next_page = None
    return redirect(next_page or url_for('dashboard.index'))

@auth.route('/email-signup', methods=['POST'])
def email_signup():
    """Handle email/password signup with plan selection"""
    try:
        email = request.form.get('email')
        password = request.form.get('password')
        full_name = request.form.get('full_name')
        plan = request.form.get('plan', 'basic')
        coupon = request.form.get('coupon', '')
        
        if not all([email, password, full_name]):
            flash('Please fill in all required fields.', 'error')
            return redirect(url_for('auth.pricing'))
        
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            flash('An account with this email already exists. Please sign in instead.', 'error')
            return redirect(url_for('auth.login'))
        
        # Map plan names to subscription tiers
        tier_map = {
            'basic': SubscriptionTier.BASIC,
            'plus': SubscriptionTier.PLUS, 
            'pro': SubscriptionTier.PRO,
            'enterprise': SubscriptionTier.ENTERPRISE
        }
        
        subscription_tier = tier_map.get(plan, SubscriptionTier.BASIC)
        
        # Handle special coupon codes
        if coupon.upper() == 'SAINTSDOMINIONSTEWARD':
            subscription_tier = SubscriptionTier.ENTERPRISE
            subscription_status = 'active'
        elif coupon.upper() == 'SAINTSDOMINION':
            subscription_status = 'trial'
        else:
            subscription_status = 'inactive'
        
        # Create new user
        user = User()
        user.email = email
        user.username = (full_name.split()[0] if full_name else email.split('@')[0]) if full_name or email else 'user'
        user.full_name = full_name
        user.password_hash = generate_password_hash(password)
        user.subscription_tier = subscription_tier
        # subscription_status will be handled by Stripe webhooks
        user.profile_completion_percentage = 25  # Basic info provided
        
        db.session.add(user)
        db.session.commit()
        
        # Log in the new user
        login_user(user)
        
        # Handle special coupons
        if coupon.upper() == 'SAINTSDOMINIONSTEWARD':
            flash('Welcome! Your lifetime Enterprise access has been activated.', 'success')
            return redirect(url_for('dashboard.index'))
        elif coupon.upper() == 'SAINTSDOMINION':
            flash('Welcome! Your 24-hour trial has started. You can cancel anytime.', 'success')
            return redirect(url_for('dashboard.index'))
        
        # For regular signups, redirect to payment
        session['selected_plan'] = plan
        session['coupon_code'] = coupon
        # For now, redirect to dashboard - Stripe integration would be implemented here
        flash('Account created successfully! Subscription setup required.', 'success')
        return redirect(url_for('dashboard.index'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Registration failed: {str(e)}', 'error')
        return redirect(url_for('auth.pricing'))

@auth.route('/demo/<tier>')
def demo_login(tier):
    """Demo login for testing all subscription tiers"""
    tier_map = {
        'basic': SubscriptionTier.BASIC,
        'plus': SubscriptionTier.PLUS,
        'pro': SubscriptionTier.PRO,
        'enterprise': SubscriptionTier.ENTERPRISE
    }
    
    if tier not in tier_map:
        flash('Invalid subscription tier', 'error')
        return redirect(url_for('auth.login'))
    
    # Find or create demo user
    demo_email = f'demo.{tier}@dominatemarketing.com'
    user = User.query.filter_by(email=demo_email).first()
    
    if not user:
        try:
            user = User()
            user.username = f'Demo {tier.title()}'
            user.email = demo_email
            user.subscription_tier = tier_map[tier]
            user.full_name = f'Demo {tier.title()} User'
            user.account_active = True
            user.is_demo_account = True
            db.session.add(user)
            db.session.commit()
        except Exception as e:
            flash(f'Demo setup error: {str(e)}', 'error')
            return redirect(url_for('auth.login'))
    
    try:
        login_user(user)
        flash(f'Logged in as {tier.title()} demo user', 'success')
        # Send the demo user to the dashboard. (Previously this targeted a
        # 'dashboard.demo_live' route that was never defined, raising a
        # BuildError on every visit; dashboard.index matches the working
        # /demo-login route in main_app.py.)
        return redirect(url_for('dashboard.index'))
    except Exception as e:
        flash(f'Login error: {str(e)}', 'error')
        return redirect(url_for('auth.login'))

@auth.route('/pricing')
def pricing():
    """Display membership tier pricing"""
    tiers = [
        {
            'name': 'Basic',
            'price': '$29/month',
            'features': [
                'AI-generated ad copy',
                'Posting time recommendations',
                'Basic competitor insights',
                'Download text content'
            ],
            'tier': 'basic'
        },
        {
            'name': 'Plus',
            'price': '$59/month', 
            'features': [
                'Everything in Basic',
                'AI-generated images',
                'Download high-res images',
                'Enhanced competitor analysis',
                'Custom image prompts'
            ],
            'tier': 'plus'
        },
        {
            'name': 'Pro',
            'price': '$99/month',
            'features': [
                'Everything in Plus',
                'AI video generation with advanced models',
                'Voice-over generation',
                'Top 5 competitor analysis',
                'Edit competitor list',
                'Download all media'
            ],
            'tier': 'pro'
        },
        {
            'name': 'Enterprise',
            'price': '$199/month',
            'features': [
                'Everything in Pro', 
                'Automated social media posting',
                'Multi-platform management',
                'Custom posting schedules',
                'Content variation controls',
                'Priority support'
            ],
            'tier': 'enterprise'
        }
    ]
    return render_template('auth/pricing.html', tiers=tiers)

@auth.route('/google_login')
def google_login():
    """Initiate Google OAuth login"""
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        flash('Google OAuth is not configured. Please use demo access.', 'error')
        return redirect(url_for('auth.login'))
    
    try:
        # Get Google OAuth configuration
        google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
        authorization_endpoint = google_provider_cfg["authorization_endpoint"]
        
        from oauthlib.oauth2 import WebApplicationClient
        client = WebApplicationClient(GOOGLE_CLIENT_ID)
        
        # Use the configured callback URL (OAUTH_CALLBACK_URL env var). It must
        # match a redirect URI registered in Google Cloud Console. Set it to the
        # Railway domain before the custom-domain cutover, then to the custom
        # domain after. Falls back to the custom domain when unset (see top of
        # file), so existing prod config keeps working without this var.
        callback_url = OAUTH_CALLBACK_URL

        request_uri = client.prepare_request_uri(
            authorization_endpoint,
            redirect_uri=callback_url,
            scope=["openid", "email", "profile"],
        )
        return redirect(request_uri)
        
    except Exception as e:
        flash(f'Google OAuth error: {str(e)}', 'error')
        return redirect(url_for('auth.login'))

@auth.route('/google_login/callback')
def google_callback():
    """Handle Google OAuth callback"""
    try:
        from oauthlib.oauth2 import WebApplicationClient
        client = WebApplicationClient(GOOGLE_CLIENT_ID)
        
        # Check for OAuth errors first
        error = request.args.get("error")
        if error:
            error_description = request.args.get("error_description", "Unknown error")
            flash(f'Google authentication failed: {error_description}', 'error')
            return redirect(url_for('auth.login'))
        
        # Get authorization code
        code = request.args.get("code")
        if not code:
            flash('No authorization code received. Please try again.', 'error')
            return redirect(url_for('auth.login'))
        
        # Get Google provider configuration
        google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
        token_endpoint = google_provider_cfg["token_endpoint"]
        
        # Exchange code for token. Must use the SAME redirect URI that was sent
        # in the authorization request (OAUTH_CALLBACK_URL), or Google rejects
        # the exchange with redirect_uri_mismatch.
        callback_url = OAUTH_CALLBACK_URL
        
        token_url, headers, body = client.prepare_token_request(
            token_endpoint,
            authorization_response=request.url.replace('http://', 'https://'),
            redirect_url=callback_url,
            code=code,
        )
        
        token_response = requests.post(
            token_url,
            headers=headers,
            data=body,
            auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET) if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET else None,
        )
        
        # Check for token response errors
        if token_response.status_code != 200:
            print(f"❌ OAuth Token Error: {token_response.status_code}")
            print(f"Response: {token_response.text}")
            flash(f'OAuth authentication failed: {token_response.text}', 'error')
            return redirect(url_for('auth.login'))
        
        # Parse the tokens
        client.parse_request_body_response(json.dumps(token_response.json()))
        
        # Get user info
        userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
        uri, headers, body = client.add_token(userinfo_endpoint)
        userinfo_response = requests.get(uri, headers=headers, data=body)
        
        userinfo = userinfo_response.json()
        
        if userinfo.get("email_verified"):
            google_id = userinfo["sub"]
            users_email = userinfo["email"]
            users_name = userinfo.get("name", userinfo.get("given_name", "User"))
            avatar_url = userinfo.get("picture")
        else:
            flash("User email not available or not verified by Google.", "error")
            return redirect(url_for('auth.login'))
        
        # Find or create user
        user = User.query.filter_by(email=users_email).first()
        
        if not user:
            # Create new user
            user = User()
            user.username = users_name
            user.email = users_email
            user.google_id = google_id
            user.avatar_url = avatar_url
            user.subscription_tier = SubscriptionTier.BASIC
            db.session.add(user)
            db.session.commit()
            flash(f'Welcome to Dominate Marketing, {users_name}!', 'success')
        else:
            # Update existing user
            user.google_id = google_id
            user.avatar_url = avatar_url
            db.session.commit()
            flash(f'Welcome back, {users_name}!', 'success')
        
        # Log in user
        login_user(user)
        user.last_login = datetime.utcnow()
        db.session.commit()

        # Redirect new users to profile completion
        if not user.onboarding_completed and user.profile_completion_percentage < 50:
            flash('Welcome! Please complete your profile to get personalized marketing campaigns.', 'info')
            return redirect(url_for('auth.profile_completion'))
        
        return redirect(url_for('dashboard.index'))
        
    except Exception as e:
        flash(f'Authentication error: {str(e)}', 'error')
        return redirect(url_for('auth.login'))



@auth.route('/profile/complete')
@login_required
def profile_completion():
    """Profile completion form for marketing data capture"""
    return render_template('auth/profile_completion.html')

@auth.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    """Update user profile with marketing information"""
    try:
        # Basic profile info
        current_user.full_name = request.form.get('full_name', current_user.full_name)
        current_user.job_title = request.form.get('job_title')
        current_user.phone_number = request.form.get('phone_number')
        current_user.country = request.form.get('country')
        
        # Business information
        current_user.company_name = request.form.get('company_name')
        current_user.industry = request.form.get('industry')
        current_user.company_size = request.form.get('company_size')
        current_user.annual_revenue = request.form.get('annual_revenue')
        
        # Marketing information
        current_user.marketing_budget = request.form.get('marketing_budget')
        current_user.how_heard_about_us = request.form.get('how_heard_about_us')
        current_user.target_audience = request.form.get('target_audience')
        current_user.marketing_goals = request.form.get('marketing_goals')
        current_user.biggest_marketing_challenge = request.form.get('biggest_marketing_challenge')
        
        # Communication preferences
        current_user.email_marketing_consent = 'email_marketing_consent' in request.form
        current_user.sms_marketing_consent = 'sms_marketing_consent' in request.form
        current_user.newsletter_subscription = 'newsletter_subscription' in request.form
        current_user.product_updates_consent = 'product_updates_consent' in request.form
        
        # Calculate profile completion percentage
        fields_filled = 0
        total_fields = 20  # Total marketing-relevant fields
        
        marketing_fields = [
            current_user.full_name, current_user.job_title, current_user.phone_number,
            current_user.company_name, current_user.industry, current_user.company_size,
            current_user.annual_revenue, current_user.marketing_budget, current_user.how_heard_about_us,
            current_user.target_audience, current_user.marketing_goals, current_user.biggest_marketing_challenge,
            current_user.country, current_user.email_marketing_consent, current_user.newsletter_subscription
        ]
        
        fields_filled = sum(1 for field in marketing_fields if field)
        current_user.profile_completion_percentage = max(20, min(100, int((fields_filled / total_fields) * 100)))
        
        # Mark onboarding as completed if profile is substantial
        if current_user.profile_completion_percentage >= 70:
            current_user.onboarding_completed = True
        
        db.session.commit()
        flash('Profile updated successfully! We can now create better targeted campaigns for you.', 'success')
        
        # Redirect to dashboard if profile is complete enough, otherwise back to completion form
        if current_user.profile_completion_percentage >= 50:
            return redirect(url_for('dashboard.index'))
        else:
            return redirect(url_for('auth.profile_completion'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating profile: {str(e)}', 'error')
        return redirect(url_for('auth.profile_completion'))

@auth.route('/marketing-export')
@login_required
def marketing_data_export():
    """Export marketing data for admin use (requires admin access)"""
    # This would be admin-only in production
    if not current_user.email.endswith('@dominatemarketing.com'):
        flash('Access denied', 'error')
        return redirect(url_for('dashboard.index'))
    
    # Get all users with marketing consent
    users_with_consent = User.query.filter(
        (User.email_marketing_consent == True) | 
        (User.newsletter_subscription == True)
    ).all()
    
    marketing_data = []
    for user in users_with_consent:
        user_data = {
            'email': user.email,
            'full_name': user.full_name,
            'phone_number': user.phone_number,
            'company_name': user.company_name,
            'industry': user.industry,
            'company_size': user.company_size,
            'annual_revenue': user.annual_revenue,
            'marketing_budget': user.marketing_budget,
            'target_audience': user.target_audience,
            'marketing_goals': user.marketing_goals,
            'biggest_challenge': user.biggest_marketing_challenge,
            'how_heard_about_us': user.how_heard_about_us,
            'country': user.country,
            'subscription_tier': user.subscription_tier.value,
            'email_consent': user.email_marketing_consent,
            'sms_consent': user.sms_marketing_consent,
            'created_at': user.created_at.isoformat() if user.created_at else None,
            'last_login': user.last_login.isoformat() if user.last_login else None
        }
        marketing_data.append(user_data)
    
    return render_template('auth/marketing_export.html', users=marketing_data, total_users=len(marketing_data))

@auth.route('/logout')
@login_required
def logout():
    """Logout user"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

# Print setup instructions when module is imported
if GOOGLE_CLIENT_ID:
    print("Google OAuth configured successfully")
else:
    print("""
    To enable Google authentication:
    1. Go to https://console.cloud.google.com/apis/credentials
    2. Create OAuth 2.0 Client ID
    3. Add authorized redirect URI
    4. Set GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET in Replit Secrets
    """)