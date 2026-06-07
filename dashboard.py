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
        # Count generated content pieces across this client's campaigns.
        total_content = sum(
            bool(c.ad_text) + bool(c.image_prompt) + bool(c.video_prompt)
            for c in campaigns
        )
        brand_stats.append({
            'brand': brand,
            'total_campaigns': len(campaigns),
            'active_campaigns': active_campaigns,
            'total_content': total_content,
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
    # Canonical client page is view_brand; keep this URL working as a redirect.
    return redirect(url_for('dashboard.view_brand', brand_id=brand_id))


def _apply_client_fields(brand):
    """Read the client (Brand) form fields and apply them to `brand`.

    Shared by create_brand and edit_brand. Returns an error message string if
    validation fails, else None.
    """
    brand_name = request.form.get('brand_name', '').strip()
    if not brand_name:
        return 'Client name is required.'

    brand.name = brand_name
    brand.website_url = request.form.get('website_url', '').strip()
    brand.industry = request.form.get('industry', '').strip()
    brand.description = request.form.get('description', '').strip()
    brand.contact_name = request.form.get('contact_name', '').strip() or None
    brand.contact_email = request.form.get('contact_email', '').strip() or None
    brand.contact_phone = request.form.get('contact_phone', '').strip() or None
    brand.notes = request.form.get('notes', '').strip() or None

    status = request.form.get('status', 'active').strip()
    brand.status = status if status in ('active', 'onboarding', 'paused', 'churned') else 'active'

    retainer = request.form.get('monthly_retainer', '').strip()
    if retainer:
        try:
            brand.monthly_retainer = float(retainer)
        except ValueError:
            brand.monthly_retainer = None
    else:
        brand.monthly_retainer = None
    return None


@dashboard_bp.route('/brand/create', methods=['GET', 'POST'])
@login_required
def create_brand():
    if request.method == 'GET':
        return render_template('dashboard/create_brand.html')

    # Tier-based client limits only apply to paying SaaS customers. Internal
    # staff (salespeople/admins) and billing-disabled mode are unlimited.
    from models import billing_disabled
    is_internal = current_user.is_salesperson or current_user.is_admin or billing_disabled()
    if not is_internal:
        tier_limits = {'basic': 1, 'plus': 3, 'pro': 10, 'enterprise': 50}
        tier_name = current_user.subscription_tier.value if current_user.subscription_tier else 'basic'
        limit = tier_limits.get(tier_name, 1)
        if Brand.query.filter_by(user_id=current_user.id).count() >= limit:
            flash(f'Client limit reached for your plan ({limit}).', 'error')
            return redirect(url_for('dashboard.index'))

    brand = Brand(user_id=current_user.id, name='')
    error = _apply_client_fields(brand)
    if error:
        flash(error, 'error')
        return redirect(url_for('dashboard.create_brand'))
    db.session.add(brand)
    db.session.commit()
    flash(f'Client "{brand.name}" added!', 'success')
    return redirect(url_for('dashboard.view_brand', brand_id=brand.id))


@dashboard_bp.route('/brand/<brand_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_brand(brand_id):
    brand = Brand.query.filter_by(id=brand_id, user_id=current_user.id).first_or_404()
    if request.method == 'GET':
        return render_template('dashboard/create_brand.html', brand=brand)
    error = _apply_client_fields(brand)
    if error:
        flash(error, 'error')
        return redirect(url_for('dashboard.edit_brand', brand_id=brand.id))
    db.session.commit()
    flash(f'Client "{brand.name}" updated!', 'success')
    return redirect(url_for('dashboard.view_brand', brand_id=brand.id))


@dashboard_bp.route('/brand/<brand_id>/view')
@login_required
def view_brand(brand_id):
    brand = Brand.query.filter_by(id=brand_id, user_id=current_user.id).first_or_404()
    campaigns = Campaign.query.filter_by(brand_id=brand.id).order_by(desc(Campaign.created_at)).all()

    # Automation panel data
    from models import SocialAccount
    social_accounts = SocialAccount.query.filter_by(brand_id=brand.id, is_active=True).all()
    upcoming_posts = SocialPost.query.join(Campaign).filter(
        Campaign.brand_id == brand.id,
        SocialPost.status == 'scheduled'
    ).order_by(SocialPost.scheduled_for).limit(20).all()
    research = json.loads(brand.research_snapshot) if brand.research_snapshot else None
    all_platforms = ['facebook', 'instagram', 'twitter', 'linkedin', 'tiktok']
    connected_platforms = {a.platform for a in social_accounts}

    return render_template('dashboard/view_brand.html', brand=brand, campaigns=campaigns,
                           social_accounts=social_accounts, upcoming_posts=upcoming_posts,
                           research=research, all_platforms=all_platforms,
                           connected_platforms=connected_platforms)


# ---------------------------------------------------------------------------
# Automation engine + social connections (per client)
# ---------------------------------------------------------------------------
def _owned_brand_or_404(brand_id):
    return Brand.query.filter_by(id=brand_id, user_id=current_user.id).first_or_404()


@dashboard_bp.route('/brand/<brand_id>/automation', methods=['POST'])
@login_required
def update_automation(brand_id):
    """Toggle automation on/off and set the posting cadence for a client."""
    brand = _owned_brand_or_404(brand_id)
    brand.automation_enabled = request.form.get('automation_enabled') == 'on'
    try:
        cadence = int(request.form.get('posting_frequency_days', 3))
        brand.posting_frequency_days = max(1, min(cadence, 30))
    except (ValueError, TypeError):
        brand.posting_frequency_days = 3
    db.session.commit()
    state = 'enabled' if brand.automation_enabled else 'paused'
    flash(f'Automation {state} for {brand.name}.', 'success')
    return redirect(url_for('dashboard.view_brand', brand_id=brand.id))


@dashboard_bp.route('/brand/<brand_id>/run-automation', methods=['POST'])
@login_required
def run_automation(brand_id):
    """Run one automation cycle now (research → generate → schedule)."""
    brand = _owned_brand_or_404(brand_id)
    from services.automation_engine import run_cycle
    try:
        summary = run_cycle(brand)
        if summary.get('posts_scheduled'):
            flash(f"Automation ran: refreshed research and scheduled "
                  f"{summary['posts_scheduled']} post(s). ({summary['mode']} mode)", 'success')
        else:
            flash(f"Automation refreshed research, but no posts were scheduled "
                  f"({summary.get('note') or 'connect a social account first'}).", 'warning')
    except Exception as e:
        logger.error(f"run_automation error: {e}")
        flash(f'Automation could not complete: {e}', 'error')
    return redirect(url_for('dashboard.view_brand', brand_id=brand.id))


@dashboard_bp.route('/brand/<brand_id>/social/connect/<platform>')
@login_required
def connect_social(brand_id, platform):
    """Connect a client's social account.

    If a real OAuth app is configured for this platform, redirect into the OAuth
    flow. Otherwise create a SIMULATED connection so the pipeline is reviewable
    end to end without real connectors.
    """
    brand = _owned_brand_or_404(brand_id)
    from models import SocialAccount
    from services.automation_engine import social_configured

    if platform not in ('facebook', 'instagram', 'twitter', 'linkedin', 'tiktok'):
        flash('Unknown platform.', 'error')
        return redirect(url_for('dashboard.view_brand', brand_id=brand.id))

    if social_configured(platform):
        # Real OAuth flow — encode brand in state so the callback can scope it.
        from services.social_auth_service import social_auth_service
        redirect_uri = url_for('dashboard.social_callback', platform=platform, _external=True)
        # Reuse the service's URL builder but carry brand_id in state.
        url = social_auth_service.get_auth_url(platform, f"{current_user.id}|{brand.id}", redirect_uri)
        if url:
            return redirect(url)
        flash(f'{platform.title()} is not fully configured; created a simulated connection instead.', 'info')

    # Simulated connection
    existing = SocialAccount.query.filter_by(brand_id=brand.id, platform=platform).first()
    if existing:
        existing.is_active = True
        existing.is_simulated = True
        existing.username = f"@{brand.name.lower().replace(' ', '')}_{platform}"
    else:
        acct = SocialAccount(
            user_id=current_user.id, brand_id=brand.id, platform=platform,
            username=f"@{brand.name.lower().replace(' ', '')}_{platform}",
            is_active=True, is_simulated=True,
        )
        db.session.add(acct)
    db.session.commit()
    flash(f'{platform.title()} connected (simulated) for {brand.name}.', 'success')
    return redirect(url_for('dashboard.view_brand', brand_id=brand.id))


@dashboard_bp.route('/social/callback/<platform>')
@login_required
def social_callback(platform):
    """Real OAuth callback — exchanges the code and stores the client's account."""
    from services.social_auth_service import social_auth_service
    code = request.args.get('code')
    state = request.args.get('state', '')
    redirect_uri = url_for('dashboard.social_callback', platform=platform, _external=True)
    result = social_auth_service.handle_oauth_callback(platform, code, state.replace('|', ':'), redirect_uri)
    # Scope the new account to the client carried in state (user_id|brand_id).
    brand_id = state.split('|')[-1] if '|' in state else None
    if result.get('success') and brand_id and result.get('account'):
        result['account'].brand_id = brand_id
        db.session.commit()
        flash(f'{platform.title()} account connected.', 'success')
    else:
        flash(f'Could not connect {platform}: {result.get("error", "unknown error")}', 'error')
    return redirect(url_for('dashboard.view_brand', brand_id=brand_id) if brand_id else url_for('dashboard.brands'))


@dashboard_bp.route('/brand/<brand_id>/social/connect-zapier', methods=['POST'])
@login_required
def connect_zapier(brand_id):
    """Connect a client's platform via a Zapier Catch Hook webhook URL.

    Real posting with no platform developer app: the user pastes the webhook URL
    from their Zap; we store it on the (client, platform) account and send posts
    there. Upserts by (brand, platform) so it replaces any prior connection.
    """
    brand = _owned_brand_or_404(brand_id)
    from models import SocialAccount
    platform = (request.form.get('platform') or '').strip().lower()
    webhook_url = (request.form.get('webhook_url') or '').strip()

    if platform not in ('facebook', 'instagram', 'twitter', 'linkedin', 'tiktok'):
        flash('Please choose a platform.', 'error')
        return redirect(url_for('dashboard.view_brand', brand_id=brand.id))
    if not (webhook_url.startswith('https://') and 'hooks.zapier.com' in webhook_url):
        flash('That doesn\'t look like a Zapier webhook URL (it should start with '
              'https://hooks.zapier.com/...).', 'error')
        return redirect(url_for('dashboard.view_brand', brand_id=brand.id))

    acct = SocialAccount.query.filter_by(brand_id=brand.id, platform=platform).first()
    if not acct:
        acct = SocialAccount(user_id=current_user.id, brand_id=brand.id, platform=platform)
        db.session.add(acct)
    acct.webhook_url = webhook_url
    acct.is_simulated = False
    acct.is_active = True
    acct.username = acct.username or f"{brand.name} {platform} (via Zapier)"
    db.session.commit()
    flash(f'{platform.title()} connected via Zapier for {brand.name}. Posts will publish for real.', 'success')
    return redirect(url_for('dashboard.view_brand', brand_id=brand.id))


@dashboard_bp.route('/social/<account_id>/disconnect', methods=['POST'])
@login_required
def disconnect_social(account_id):
    from models import SocialAccount
    acct = SocialAccount.query.filter_by(id=account_id, user_id=current_user.id).first_or_404()
    brand_id = acct.brand_id
    acct.is_active = False
    db.session.commit()
    flash(f'{acct.platform.title()} disconnected.', 'info')
    return redirect(url_for('dashboard.view_brand', brand_id=brand_id) if brand_id else url_for('dashboard.brands'))


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


def _create_campaign_from_form(brand_id=None):
    """Create a Campaign from the submitted form and kick off generation.

    Shared by the brand-scoped flow (new_campaign_form) and the standalone
    flow (create_campaign_post). The two templates use slightly different field
    names, so we accept either. brand_id is optional — Campaign.brand_id is
    nullable, so a campaign can be created without a client attached.
    """
    form = request.form
    # Accept either form's field names.
    campaign_title = (form.get('campaign_name') or form.get('title') or '').strip() \
        or f"Campaign {datetime.utcnow().strftime('%b %d')}"
    target_url = (form.get('target_url') or form.get('business_url') or '').strip()
    target_audience = form.get('target_audience', '').strip()
    campaign_goal = form.get('campaign_goal', 'engagement').strip()
    brand_voice = form.get('brand_voice', 'professional').strip()
    content_types = form.getlist('content_types') or ['text', 'image']

    # Resolve/validate the brand if one was supplied (from the URL or the form).
    brand_id = brand_id or form.get('brand_id') or None
    if brand_id:
        brand = Brand.query.filter_by(id=brand_id, user_id=current_user.id).first()
        if not brand:
            brand_id = None  # ignore a brand that isn't this user's

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
        # Record the tier in effect when the campaign was created.
        tier_used=getattr(current_user.subscription_tier, 'value', 'basic'),
        # Persist content-type selection on an existing column (there is no
        # dedicated content_preferences column on the model).
        services_used=json.dumps({'content_types': content_types}),
    )
    db.session.add(campaign)
    db.session.commit()

    # Kick off async generation. Guarded so a missing AI key / processor never
    # 500s the request — the campaign is still created and can be regenerated.
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
        flash('Campaign created. AI generation is not configured yet, so no content was generated.', 'warning')

    return redirect(url_for('dashboard.campaign_status', campaign_id=campaign.id))


@dashboard_bp.route('/brand/<brand_id>/new_campaign', methods=['GET', 'POST'])
@login_required
def new_campaign_form(brand_id):
    brand = Brand.query.filter_by(id=brand_id, user_id=current_user.id).first_or_404()
    if request.method == 'GET':
        return render_template('dashboard/new_campaign.html', brand=brand)
    return _create_campaign_from_form(brand_id=brand_id)


@dashboard_bp.route('/campaign/create', methods=['GET'])
@login_required
def create_campaign():
    """Standalone campaign creation form (client/brand optional)."""
    brands = Brand.query.filter_by(user_id=current_user.id, is_active=True).all()
    return render_template('dashboard/create_campaign.html', brands=brands)


@dashboard_bp.route('/campaign/create', methods=['POST'])
@login_required
def create_campaign_post():
    """Handle the standalone campaign creation form submission."""
    return _create_campaign_from_form()


@dashboard_bp.route('/campaign/<campaign_id>/status')
@login_required
def campaign_status(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    if campaign.user_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('dashboard.index'))
    # Map the campaign's status onto the shape the template expects. The
    # template treats 'queued'/'processing' as in-progress states.
    status_map = {'pending': 'queued', 'draft': 'queued'}
    job_status = {
        'status': status_map.get(campaign.status, campaign.status),
        'created_at': campaign.created_at,
    }
    return render_template('dashboard/campaign_status.html',
                           campaign=campaign,
                           job_status=job_status)


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
    # Social accounts are managed per client. Show an overview of each client and
    # the platforms they have connected, linking to the client page to manage.
    brands = Brand.query.filter_by(user_id=current_user.id).all()
    overview = []
    for b in brands:
        accts = SocialAccount.query.filter_by(brand_id=b.id, is_active=True).all()
        overview.append({'brand': b, 'platforms': [a.platform for a in accts]})
    return render_template('dashboard/social_accounts.html', overview=overview)


@dashboard_bp.route('/scheduling')
@login_required
def social_scheduling():
    posts = SocialPost.query.join(Campaign).filter(
        Campaign.user_id == current_user.id
    ).order_by(SocialPost.scheduled_for).all()
    from models import SocialAccount
    # Template looks up connected accounts by platform name.
    social_accounts = {
        a.platform: a
        for a in SocialAccount.query.filter_by(user_id=current_user.id).all()
    }
    stats = {
        'scheduled': sum(1 for p in posts if p.status == 'scheduled'),
        'posted': sum(1 for p in posts if p.status == 'posted'),
        'failed': sum(1 for p in posts if p.status == 'failed'),
        'recurring': sum(1 for p in posts if getattr(p, 'is_recurring', False)),
    }
    return render_template('dashboard/social_scheduling.html',
                           posts=posts,
                           social_accounts=social_accounts,
                           stats=stats)


# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------
@dashboard_bp.route('/analytics')
@login_required
def analytics():
    campaigns = Campaign.query.filter_by(user_id=current_user.id).order_by(desc(Campaign.created_at)).all()

    # Summary counts the template renders as headline stats.
    total_campaigns = len(campaigns)
    completed_campaigns = sum(1 for c in campaigns if c.status == 'completed')
    processing_campaigns = sum(1 for c in campaigns if c.status == 'processing')

    # Breakdown of campaigns by goal (drives the "Campaign Goals" chart).
    goals_breakdown = {}
    for c in campaigns:
        goal = (c.campaign_goal or 'general')
        goals_breakdown[goal] = goals_breakdown.get(goal, 0) + 1

    # Static comparison figures used by the "vs. traditional agency" callout.
    industry_stats = {
        'avg_agency_time_weeks': 6,
        'dominate_time_minutes': 10,
        'avg_agency_cost_monthly': 5000,
        'dominate_cost_monthly': 99,
        'traditional_data_age_years': 2,
        'trend_data_age_hours': 24,
        'update_frequency_minutes': 60,
    }

    return render_template(
        'dashboard/analytics.html',
        campaigns=campaigns,
        total_campaigns=total_campaigns,
        completed_campaigns=completed_campaigns,
        processing_campaigns=processing_campaigns,
        goals_breakdown=goals_breakdown,
        industry_stats=industry_stats,
    )


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
    # Which model each AI service uses for the current user's tier. Shown on the
    # status page; these are display strings, not wired to live calls.
    tier_models = {
        'openai': 'gpt-4o',
        'anthropic': 'claude-3-5-sonnet',
        'google_ai': 'gemini-1.5-pro',
    }
    tier = getattr(current_user.subscription_tier, 'value', 'basic')
    tier_color = {
        'basic': 'secondary',
        'plus': 'info',
        'pro': 'primary',
        'enterprise': 'success',
    }.get(tier, 'secondary')
    # Feature capabilities for the current tier (drives the feature matrix and
    # the video-generation sections in the template).
    from models import SubscriptionTier
    capabilities = {
        'text_generation': True,
        'image_generation': current_user.can_access_tier(SubscriptionTier.PLUS),
        'competitor_analysis': current_user.can_access_tier(SubscriptionTier.PRO),
        'video_generation': current_user.can_access_tier(SubscriptionTier.PRO),
        'image_to_video': current_user.can_access_tier(SubscriptionTier.PRO),
        'auto_posting': current_user.can_access_tier(SubscriptionTier.ENTERPRISE),
    }
    # Per-service "is it configured?" booleans the template checks individually.
    service_status = {
        'openai': bool(os.environ.get('OPENAI_API_KEY')),
        'anthropic': bool(os.environ.get('ANTHROPIC_API_KEY')),
        'google': bool(os.environ.get('GOOGLE_API_KEY')),
        'pika_labs': bool(os.environ.get('PIKA_LABS_API_KEY')),
    }
    # Rough time estimate breakdown shown on the status page.
    processing_estimate = {
        'estimated_minutes': 5,
        'breakdown': {
            'Website analysis': '~1 min',
            'Strategy generation': '~1 min',
            'Content creation': '~2 min',
            'Quality review': '~1 min',
        },
    }
    return render_template('dashboard/ai_services_status.html',
                           status=status,
                           tier_models=tier_models,
                           tier_color=tier_color,
                           capabilities=capabilities,
                           service_status=service_status,
                           processing_estimate=processing_estimate)


@dashboard_bp.route('/tone-examples')
@login_required
def tone_examples():
    """Static page of brand-voice / tone examples."""
    return render_template('dashboard/tone_examples.html')
