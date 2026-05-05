"""
User Dashboard - Brand and Campaign Management System
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import json
import uuid
import logging
import os
from models import db, User, Brand, Campaign, SocialPost, Competitor
from sqlalchemy import desc

logger = logging.getLogger(__name__)
dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')


# ---------------------------------------------------------------------------
# Dashboard index
# ---------------------------------------------------------------------------
@dashboard_bp.route('/')
@login_required
def index():
    brands = Brand.query.filter_by(user_id=current_user.id).all()
    brand_stats = []
    for brand in brands:
        campaigns = Campaign.query.filter_by(brand_id=brand.id).order_by(desc(Campaign.created_at)).all()
        active_campaigns = len([c for c in campaigns if c.status == 'completed'])
        scheduled_posts = SocialPost.query.join(Campaign).filter(
            Campaign.brand_id == brand.id,
            SocialPost.scheduled_for > datetime.utcnow()
        ).count()
        brand_stats.append({
            'brand': brand,
            'total_campaigns': len(campaigns),
            'active_campaigns': active_campaigns,
            'scheduled_posts': scheduled_posts,
            'last_campaign': campaigns[0] if campaigns else None,
        })
    return render_template('dashboard/index.html', brand_stats=brand_stats)


# ---------------------------------------------------------------------------
# Brand routes
# ---------------------------------------------------------------------------
@dashboard_bp.route('/brand/<brand_id>')
@login_required
def brand_detail(brand_id):
    brand = Brand.query.filter_by(id=brand_id, user_id=current_user.id).first_or_404()
    campaigns = Campaign.query.filter_by(brand_id=brand_id).order_by(desc(Campaign.created_at)).all()
    campaign_data = []
    for campaign in campaigns:
        scheduled_posts = SocialPost.query.filter_by(campaign_id=campaign.id).all()
        content_data = json.loads(campaign.ai_content) if campaign.ai_content else {}
        campaign_data.append({
            'campaign': campaign,
            'content_summary': {
                'images': len(content_data.get('images', [])),
                'videos': len(content_data.get('videos', [])),
                'texts': len(content_data.get('texts', [])),
            },
            'scheduling_summary': {
                'pending': len([p for p in scheduled_posts if p.status == 'scheduled']),
                'published': len([p for p in scheduled_posts if p.status == 'posted']),
                'total': len(scheduled_posts),
            },
        })
    return render_template('dashboard/brand_detail.html', brand=brand, campaign_data=campaign_data)


@dashboard_bp.route('/brand/create', methods=['GET', 'POST'])
@login_required
def create_brand():
    if request.method == 'GET':
        return render_template('dashboard/create_brand.html')

    brand_name = request.form.get('brand_name', '').strip()
    website_url = request.form.get('website_url', '').strip()
    industry = request.form.get('industry', '').strip()
    description = request.form.get('description', '').strip()

    if not brand_name:
        flash('Brand name is required.', 'error')
        return redirect(url_for('dashboard.create_brand'))

    # Enforce tier limits
    tier_limits = {'basic': 1, 'plus': 3, 'pro': 10, 'enterprise': 50}
    tier_name = current_user.subscription_tier.value if current_user.subscription_tier else 'basic'
    limit = tier_limits.get(tier_name, 1)
    current_count = Brand.query.filter_by(user_id=current_user.id).count()
    if current_count >= limit:
        flash(f'Brand limit reached for your plan ({limit}). Upgrade to add more brands.', 'error')
        return redirect(url_for('dashboard.index'))

    brand = Brand(
        user_id=current_user.id,
        name=brand_name,
        website_url=website_url,
        industry=industry,
        description=description,
    )
    db.session.add(brand)
    db.session.commit()
    flash(f'Brand "{brand_name}" created!', 'success')
    return redirect(url_for('dashboard.index'))


@dashboard_bp.route('/brand/<brand_id>/view')
@login_required
def view_brand(brand_id):
    brand = Brand.query.filter_by(id=brand_id, user_id=current_user.id).first_or_404()
    campaigns = Campaign.query.filter_by(brand_id=brand.id).order_by(desc(Campaign.created_at)).all()
    return render_template('dashboard/view_brand.html', brand=brand, campaigns=campaigns)


# ---------------------------------------------------------------------------
# Campaign routes
# ---------------------------------------------------------------------------
@dashboard_bp.route('/campaign/<campaign_id>')
@login_required
def campaign_detail(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    if campaign.user_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('dashboard.index'))
    content_data = json.loads(campaign.ai_content) if campaign.ai_content else {}
    scheduled_posts = SocialPost.query.filter_by(campaign_id=campaign_id).order_by(SocialPost.scheduled_for).all()
    content_by_type = {
        'images': content_data.get('images', []),
        'videos': content_data.get('videos', []),
        'texts': content_data.get('texts', []),
    }
    return render_template('dashboard/campaign_detail.html',
                           campaign=campaign,
                           content_by_type=content_by_type,
                           scheduled_posts=scheduled_posts)


@dashboard_bp.route('/brand/<brand_id>/new_campaign', methods=['GET', 'POST'])
@login_required
def new_campaign_form(brand_id):
    brand = Brand.query.filter_by(id=brand_id, user_id=current_user.id).first_or_404()
    if request.method == 'GET':
        return render_template('dashboard/new_campaign.html', brand=brand)

    # POST — create and kick off generation
    campaign_title = request.form.get('campaign_name', '').strip() or f"Campaign {datetime.utcnow().strftime('%b %d')}"
    target_url = request.form.get('target_url', '').strip()
    target_audience = request.form.get('target_audience', '').strip()
    campaign_goal = request.form.get('campaign_goal', 'engagement').strip()
    brand_voice = request.form.get('brand_voice', 'professional').strip()
    content_types = request.form.getlist('content_types') or ['text', 'image']

    campaign = Campaign(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        brand_id=brand_id,
        title=campaign_title,
        business_url=target_url,
        target_url=target_url,
        target_audience=target_audience,
        campaign_goal=campaign_goal,
        brand_voice=brand_voice,
        status='pending',
        content_preferences=json.dumps({'content_types': content_types}),
    )
    db.session.add(campaign)
    db.session.commit()

    # Kick off async generation
    try:
        from services.async_campaign_processor import AsyncCampaignProcessor
        processor = AsyncCampaignProcessor()
        processor.queue_campaign(campaign.id, {
            'url': target_url,
            'audience': target_audience,
            'goal': campaign_goal,
            'brand_voice': brand_voice,
            'content_types': content_types,
        })
        flash(f'Campaign "{campaign_title}" created! Content is generating in the background.', 'success')
    except Exception as e:
        logger.error(f"Failed to queue campaign generation: {e}")
        flash(f'Campaign created but generation could not start automatically. Error: {e}', 'warning')

    return redirect(url_for('dashboard.campaign_status', campaign_id=campaign.id))


@dashboard_bp.route('/campaign/<campaign_id>/status')
@login_required
def campaign_status(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    if campaign.user_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('dashboard.index'))
    return render_template('dashboard/campaign_status.html', campaign=campaign)


@dashboard_bp.route('/api/campaign/<campaign_id>/status')
@login_required
def campaign_status_api(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    if campaign.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    return jsonify({
        'status': campaign.status,
        'title': campaign.title,
        'has_content': bool(campaign.ai_content),
    })


# ---------------------------------------------------------------------------
# Content regeneration
# ---------------------------------------------------------------------------
@dashboard_bp.route('/campaign/<campaign_id>/regenerate', methods=['POST'])
@login_required
def regenerate_content(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    if campaign.user_id != current_user.id:
        return jsonify({'success': False, 'error': 'Access denied'})

    content_type = request.form.get('content_type', 'text')  # text / image / video
    feedback = request.form.get('feedback', '')

    try:
        from services.user_campaign_generator import UserCampaignGenerator
        generator = UserCampaignGenerator()
        result = generator.regenerate_content_type(campaign_id, content_type, feedback)
        if result.get('success'):
            return jsonify({'success': True, 'message': f'{content_type.title()} content regenerated successfully.'})
        return jsonify({'success': False, 'error': result.get('error', 'Regeneration failed')})
    except Exception as e:
        logger.error(f"Regeneration failed for campaign {campaign_id}: {e}")
        return jsonify({'success': False, 'error': str(e)})


# ---------------------------------------------------------------------------
# Support requests
# ---------------------------------------------------------------------------
@dashboard_bp.route('/campaign/<campaign_id>/support', methods=['POST'])
@login_required
def contact_support(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    if campaign.user_id != current_user.id:
        return jsonify({'success': False, 'error': 'Access denied'})

    issue_type = request.form.get('issue_type', 'quality')
    description = request.form.get('description', '')

    support_data = {
        'user_id': current_user.id,
        'user_email': current_user.email,
        'campaign_id': campaign_id,
        'campaign_title': campaign.title,
        'issue_type': issue_type,
        'description': description,
        'timestamp': datetime.utcnow().isoformat(),
    }
    try:
        with open('support_requests.jsonl', 'a') as f:
            f.write(json.dumps(support_data) + '\n')
    except Exception as e:
        logger.error(f"Could not write support request: {e}")

    flash('Support request submitted. We\'ll respond within 24 hours.', 'success')
    return redirect(url_for('dashboard.campaign_detail', campaign_id=campaign_id))


# ---------------------------------------------------------------------------
# Campaign stats API
# ---------------------------------------------------------------------------
@dashboard_bp.route('/api/campaign_stats/<campaign_id>')
@login_required
def campaign_stats(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    if campaign.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403

    content_data = json.loads(campaign.ai_content) if campaign.ai_content else {}
    return jsonify({
        'total_content': sum(len(v) for v in content_data.values() if isinstance(v, list)),
        'by_type': {
            'images': len(content_data.get('images', [])),
            'videos': len(content_data.get('videos', [])),
            'texts': len(content_data.get('texts', [])),
        },
        'status': campaign.status,
        'last_updated': campaign.updated_at.isoformat() if hasattr(campaign, 'updated_at') and campaign.updated_at else None,
    })


# ---------------------------------------------------------------------------
# Brands list
# ---------------------------------------------------------------------------
@dashboard_bp.route('/brands')
@login_required
def brands():
    all_brands = Brand.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard/brands.html', brands=all_brands)


# ---------------------------------------------------------------------------
# Social scheduling
# ---------------------------------------------------------------------------
@dashboard_bp.route('/social')
@login_required
def social_accounts():
    from models import SocialAccount
    accounts = SocialAccount.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard/social_accounts.html', accounts=accounts)


@dashboard_bp.route('/scheduling')
@login_required
def social_scheduling():
    posts = SocialPost.query.join(Campaign).filter(
        Campaign.user_id == current_user.id
    ).order_by(SocialPost.scheduled_for).all()
    return render_template('dashboard/social_scheduling.html', posts=posts)


# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------
@dashboard_bp.route('/analytics')
@login_required
def analytics():
    campaigns = Campaign.query.filter_by(user_id=current_user.id).order_by(desc(Campaign.created_at)).all()
    return render_template('dashboard/analytics.html', campaigns=campaigns)


# ---------------------------------------------------------------------------
# Gallery
# ---------------------------------------------------------------------------
@dashboard_bp.route('/gallery')
@login_required
def gallery():
    campaigns = Campaign.query.filter_by(
        user_id=current_user.id, status='completed'
    ).order_by(desc(Campaign.created_at)).all()
    all_content = []
    for c in campaigns:
        data = json.loads(c.ai_content) if c.ai_content else {}
        for img in data.get('images', []):
            all_content.append({'type': 'image', 'campaign': c, 'data': img})
        for vid in data.get('videos', []):
            all_content.append({'type': 'video', 'campaign': c, 'data': vid})
        for txt in data.get('texts', []):
            all_content.append({'type': 'text', 'campaign': c, 'data': txt})
    return render_template('dashboard/gallery.html', content_items=all_content)


# ---------------------------------------------------------------------------
# AI Services status
# ---------------------------------------------------------------------------
@dashboard_bp.route('/ai-status')
@login_required
def ai_services_status():
    status = {}
    try:
        import openai
        status['openai'] = 'configured' if os.environ.get('OPENAI_API_KEY') else 'missing key'
    except ImportError:
        status['openai'] = 'not installed'
    try:
        import anthropic
        status['anthropic'] = 'configured' if os.environ.get('ANTHROPIC_API_KEY') else 'missing key'
    except ImportError:
        status['anthropic'] = 'not installed'
    try:
        import google.generativeai
        status['google_ai'] = 'configured' if os.environ.get('GOOGLE_API_KEY') else 'missing key'
    except ImportError:
        status['google_ai'] = 'not installed'
    return render_template('dashboard/ai_services_status.html', status=status)
