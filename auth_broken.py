from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from models import User, db, SubscriptionTier
import requests
import json
import os
from datetime import datetime

auth = Blueprint('auth', __name__)

# Google OAuth configuration
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_OAUTH_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET")
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

@auth.route('/login', methods=['GET', 'POST'])
def login():
    """Display login options or handle demo login"""
    if request.method == 'POST':
        # Demo login functionality
        demo_type = request.form.get('demo_type', 'basic')
        
        # Create or get demo user
        demo_email = f"demo.{demo_type}@dominatemarketing.com"
        demo_user = User.query.filter_by(email=demo_email).first()
        
        if not demo_user:
            # Create demo user with appropriate tier
            tier_mapping = {
                'basic': SubscriptionTier.BASIC,
                'plus': SubscriptionTier.PLUS,
                'pro': SubscriptionTier.PRO,
                'enterprise': SubscriptionTier.ENTERPRISE
            }
            
            demo_user = User(
                username=f"Demo {demo_type.title()} User",
                email=demo_email,
                subscription_tier=tier_mapping.get(demo_type, SubscriptionTier.BASIC),
                is_demo_account=True
            )
            db.session.add(demo_user)
            db.session.commit()
        
        login_user(demo_user)
        flash(f'Logged in as {demo_type.title()} demo user!', 'success')
        return redirect(url_for('dashboard.index'))
    
    return render_template('auth/login.html')

@auth.route('/signup')
def signup():
    """Display signup options with membership tiers"""
    return render_template('auth/signup.html')

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
        
        # Generate authorization URL
        request_uri = client.prepare_request_uri(
            authorization_endpoint,
            redirect_uri=request.url_root + "auth/google_login/callback",
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
        
        # Get authorization code
        code = request.args.get("code")
        if not code:
            flash('Authorization failed. Please try again.', 'error')
            return redirect(url_for('auth.login'))
        
        # Get Google provider configuration
        google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
        token_endpoint = google_provider_cfg["token_endpoint"]
        
        # Exchange code for token
        token_url, headers, body = client.prepare_token_request(
            token_endpoint,
            authorization_response=request.url,
            redirect_url=request.base_url,
            code=code,
        )
        
        token_response = requests.post(
            token_url,
            headers=headers,
            data=body,
            auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
        )
        
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
            user = User(
                username=users_name,
                email=users_email,
                google_id=google_id,
                avatar_url=avatar_url,
                subscription_tier=SubscriptionTier.BASIC
            )
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
        return redirect(url_for('dashboard.index'))
        
    except Exception as e:
        flash(f'Authentication error: {str(e)}', 'error')
        return redirect(url_for('auth.login'))

@auth.route('/logout')
@login_required
def logout():
    """Logout user"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))
        
        # Get Google's OAuth2 configuration
        google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
        token_endpoint = google_provider_cfg["token_endpoint"]
        userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
        
        # Exchange code for tokens
        token_data = {
            'client_id': GOOGLE_CLIENT_ID,
            'client_secret': GOOGLE_CLIENT_SECRET,
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': url_for('auth.google_callback', _external=True)
        }
        
        token_response = requests.post(token_endpoint, data=token_data)
        token_json = token_response.json()
        
        if 'access_token' not in token_json:
            flash('Failed to get access token', 'error')
            return redirect(url_for('auth.login'))
        
        # Get user info
        headers = {'Authorization': f"Bearer {token_json['access_token']}"}
        userinfo_response = requests.get(userinfo_endpoint, headers=headers)
        userinfo = userinfo_response.json()
        
        if not userinfo.get('email_verified'):
            flash('Email not verified with Google', 'error')
            return redirect(url_for('auth.login'))
        
        # Find or create user
        user = User.query.filter_by(email=userinfo['email']).first()
        
        if not user:
            # Create new user
            user = User(
                email=userinfo['email'],
                username=userinfo.get('given_name', userinfo['email'].split('@')[0]),
                full_name=userinfo.get('name'),
                avatar_url=userinfo.get('picture'),
                google_id=userinfo.get('sub'),
                subscription_tier=SubscriptionTier.BASIC  # Default to basic
            )
            db.session.add(user)
        else:
            # Update existing user
            if not user.google_id:
                user.google_id = userinfo.get('sub')
            user.avatar_url = userinfo.get('picture')
            user.last_login = datetime.utcnow()
        
        db.session.commit()
        login_user(user)
        
        flash(f'Welcome, {user.full_name or user.username}!', 'success')
        
        # Redirect to subscription selection if new user
        if not user.has_active_subscription():
            return redirect(url_for('auth.pricing'))
        
        return redirect(url_for('dashboard.index'))
        
    except Exception as e:
        flash(f'Login error: {str(e)}', 'error')
        return redirect(url_for('auth.login'))

@auth.route('/logout')
@login_required
def logout():
    """Log out current user"""
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

@auth.route('/profile')
@login_required
def profile():
    """User profile page"""
    return render_template('auth/profile.html', user=current_user)

@auth.route('/profile', methods=['POST'])
@login_required
def update_profile():
    """Update user profile"""
    try:
        current_user.username = request.form.get('username', current_user.username)
        current_user.full_name = request.form.get('full_name', current_user.full_name)
        current_user.company_name = request.form.get('company_name', current_user.company_name)
        current_user.industry = request.form.get('industry', current_user.industry)
        
        # Handle file upload for business document
        if 'business_document' in request.files:
            file = request.files['business_document']
            if file and file.filename:
                # Save file logic here
                # filename = secure_filename(file.filename)
                # file.save(os.path.join('uploads', 'documents', current_user.id, filename))
                # current_user.business_document_path = filename
                pass
        
        db.session.commit()
        flash('Profile updated successfully', 'success')
        
    except Exception as e:
        flash(f'Error updating profile: {str(e)}', 'error')
    
    return redirect(url_for('auth.profile'))

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