"""
Admin Dashboard Module for Dominate Marketing
Provides comprehensive administrative controls and reporting
"""
import os
import csv
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from io import StringIO, BytesIO
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, make_response, session
from flask_login import login_required, current_user
from sqlalchemy import func, desc, asc, case
from werkzeug.utils import secure_filename

from werkzeug.security import generate_password_hash

from models import db, User, Brand, Campaign, SocialPost, QualityCheck, SubscriptionTier
from services.admin_notifications import AdminNotificationService

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def is_admin():
    """Check if current user has admin privileges.

    Primary check is the User.is_admin DB column (set by bootstrap-admin or
    promoted via the /admin/salespeople UI). The legacy email allowlist is
    kept as a fallback so the original quality@/admin@dominatemarketing.com
    accounts and the ADMIN_EMAIL env var still work during the transition.
    """
    if not current_user.is_authenticated:
        return False

    if getattr(current_user, 'is_admin', False):
        return True

    admin_emails = [
        'admin@dominatemarketing.com',
        'quality@dominatemarketing.com',
    ]
    if os.environ.get('ADMIN_EMAIL'):
        admin_emails.append(os.environ.get('ADMIN_EMAIL'))
    return current_user.email in admin_emails

def admin_required(f):
    """Decorator to require admin access"""
    from functools import wraps
    @wraps(f)
    def admin_decorated_function(*args, **kwargs):
        if not is_admin():
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return admin_decorated_function

@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    """Main admin dashboard"""
    
    try:
        # Get overview statistics
        stats = get_dashboard_stats()
        
        # Get recent activity
        recent_activity = get_recent_activity()
        
        # Get quality control metrics
        quality_metrics = get_quality_metrics()
        
        # Get user engagement data
        user_metrics = get_user_metrics()
        
        return render_template('admin/dashboard.html',
                             stats=stats,
                             recent_activity=recent_activity,
                             quality_metrics=quality_metrics,
                             user_metrics=user_metrics)
    
    except Exception as e:
        logging.error(f"Admin dashboard error: {e}")
        return render_template('admin/dashboard.html',
                             error="Failed to load dashboard data")

@admin_bp.route('/reports')
@login_required
@admin_required
def reports():
    """Reports generation interface"""
    
    try:
        # Get available report types and filters
        report_config = get_report_configuration()
        
        return render_template('admin/reports.html',
                             report_config=report_config)
    
    except Exception as e:
        logging.error(f"Admin reports error: {e}")
        return render_template('admin/reports.html',
                             error="Failed to load reports interface")

@admin_bp.route('/communications')
@login_required
@admin_required
def communications():
    """User communications interface"""
    
    try:
        # Get user list for targeted communications
        users = User.query.order_by(User.created_at.desc()).all()
        
        # Get communication templates
        templates = get_communication_templates()
        
        return render_template('admin/communications.html',
                             users=users,
                             templates=templates)
    
    except Exception as e:
        logging.error(f"Admin communications error: {e}")
        return render_template('admin/communications.html',
                             error="Failed to load communications interface")

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    """User management interface"""
    
    try:
        # Get paginated user list with filters
        page = request.args.get('page', 1, type=int)
        per_page = 50
        
        users_query = User.query
        
        # Apply filters
        search = request.args.get('search', '').strip()
        if search:
            users_query = users_query.filter(
                User.email.contains(search) | 
                User.username.contains(search)
            )
        
        tier_filter = request.args.get('tier', '').strip()
        if tier_filter:
            users_query = users_query.filter(User.subscription_tier == tier_filter)
        
        users_pagination = users_query.order_by(User.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Get user statistics
        user_stats = get_detailed_user_stats()
        
        return render_template('admin/users.html',
                             users=users_pagination.items,
                             pagination=users_pagination,
                             user_stats=user_stats,
                             search=search,
                             tier_filter=tier_filter)
    
    except Exception as e:
        logging.error(f"Admin users error: {e}")
        return render_template('admin/users.html',
                             error="Failed to load users data")

@admin_bp.route('/salespeople', methods=['GET'])
@login_required
@admin_required
def salespeople():
    """List every internal account (salesperson + admin) with management controls."""
    accounts = (
        User.query
        .filter((User.is_salesperson == True) | (User.is_admin == True))  # noqa: E712
        .order_by(User.is_admin.desc(), User.created_at.desc())
        .all()
    )
    # Resolve who created each account (for audit display).
    creator_ids = {a.created_by_admin_id for a in accounts if a.created_by_admin_id}
    creators = {u.id: u for u in User.query.filter(User.id.in_(creator_ids)).all()} if creator_ids else {}
    return render_template('admin/salespeople.html', accounts=accounts, creators=creators)


@admin_bp.route('/salespeople/create', methods=['POST'])
@login_required
@admin_required
def create_salesperson():
    """Create a salesperson or admin account from the management UI."""
    username = (request.form.get('username') or '').strip()
    email = (request.form.get('email') or '').strip() or None
    password = request.form.get('password') or ''
    role = (request.form.get('role') or 'salesperson').strip()

    from flask import flash

    if not username or not password:
        flash('Username and password are required.', 'error')
        return redirect(url_for('admin.salespeople'))

    if role not in ('salesperson', 'admin'):
        flash('Role must be either "salesperson" or "admin".', 'error')
        return redirect(url_for('admin.salespeople'))

    if User.query.filter_by(username=username).first():
        flash(f'Username "{username}" is already taken.', 'error')
        return redirect(url_for('admin.salespeople'))

    if email and User.query.filter_by(email=email).first():
        flash(f'Email "{email}" is already in use.', 'error')
        return redirect(url_for('admin.salespeople'))

    new_user = User(
        username=username,
        email=email,
        password_hash=generate_password_hash(password),
        full_name=username,
        is_admin=(role == 'admin'),
        is_salesperson=(role == 'salesperson'),
        # ENTERPRISE so any service that reads subscription_tier directly gets
        # the highest level — short-circuit in can_access_tier handles the rest.
        subscription_tier=SubscriptionTier.ENTERPRISE,
        account_active=True,
        profile_completion_percentage=100,
        onboarding_completed=True,
        created_by_admin_id=current_user.id,
    )
    db.session.add(new_user)
    db.session.commit()
    flash(f'Created {role} account "{username}".', 'success')
    return redirect(url_for('admin.salespeople'))


@admin_bp.route('/salespeople/<user_id>/deactivate', methods=['POST'])
@login_required
@admin_required
def deactivate_salesperson(user_id):
    """Deactivate (soft-disable) an internal account. Never deletes the row.

    Cascade rule: the User → Brand/Campaign/SocialAccount/Competitor cascade
    is `all, delete-orphan`. A real DELETE on this user would wipe their
    entire client book. Setting account_active=False preserves all data and
    just blocks login (account_active is checked at login time).
    """
    target = User.query.get_or_404(user_id)
    from flask import flash
    if target.id == current_user.id:
        flash('You cannot deactivate your own account.', 'error')
        return redirect(url_for('admin.salespeople'))
    # Last-active-admin guard: refuse if deactivating this user would leave
    # zero active admins. Same pattern as the role-toggle guard.
    if target.is_admin and target.account_active:
        active_admin_count = User.query.filter_by(is_admin=True, account_active=True).count()
        if active_admin_count <= 1:
            flash('Cannot deactivate the last remaining active admin.', 'error')
            return redirect(url_for('admin.salespeople'))
    target.account_active = False
    db.session.commit()
    flash(f'Deactivated "{target.username}". The account row and their client data are preserved.', 'info')
    return redirect(url_for('admin.salespeople'))


@admin_bp.route('/salespeople/<user_id>/reactivate', methods=['POST'])
@login_required
@admin_required
def reactivate_salesperson(user_id):
    """Re-enable a previously deactivated internal account."""
    target = User.query.get_or_404(user_id)
    target.account_active = True
    db.session.commit()
    from flask import flash
    flash(f'Reactivated "{target.username}".', 'success')
    return redirect(url_for('admin.salespeople'))


@admin_bp.route('/salespeople/<user_id>/role', methods=['POST'])
@login_required
@admin_required
def change_salesperson_role(user_id):
    """Promote a salesperson to admin or demote an admin to salesperson."""
    target = User.query.get_or_404(user_id)
    new_role = (request.form.get('role') or '').strip()
    from flask import flash

    if new_role not in ('salesperson', 'admin'):
        flash('Role must be either "salesperson" or "admin".', 'error')
        return redirect(url_for('admin.salespeople'))

    if target.id == current_user.id and new_role != 'admin':
        flash('You cannot demote your own admin account.', 'error')
        return redirect(url_for('admin.salespeople'))

    # Last-active-admin guard: never let the system end up with zero admins
    # who can actually sign in. Deactivated admins don't count.
    if target.is_admin and new_role != 'admin':
        active_admin_count = User.query.filter_by(is_admin=True, account_active=True).count()
        if active_admin_count <= 1:
            flash('Cannot demote the last remaining active admin.', 'error')
            return redirect(url_for('admin.salespeople'))

    target.is_admin = (new_role == 'admin')
    target.is_salesperson = (new_role == 'salesperson')
    db.session.commit()
    flash(f'Set "{target.username}" role to {new_role}.', 'success')
    return redirect(url_for('admin.salespeople'))


@admin_bp.route('/quality-control')
@login_required
@admin_required
def quality_control():
    """Quality control monitoring interface"""
    
    try:
        # Get quality control overview
        quality_overview = get_quality_control_overview()
        
        # Get recent quality checks
        recent_checks = QualityCheck.query.order_by(QualityCheck.created_at.desc()).limit(50).all()
        
        # Get quality trends
        quality_trends = get_quality_trends()
        
        return render_template('admin/quality_control.html',
                             quality_overview=quality_overview,
                             recent_checks=recent_checks,
                             quality_trends=quality_trends)
    
    except Exception as e:
        logging.error(f"Admin quality control error: {e}")
        return render_template('admin/quality_control.html',
                             error="Failed to load quality control data")

# API Endpoints for Admin Functions

@admin_bp.route('/api/generate-report', methods=['POST'])
@login_required
@admin_required
def generate_report():
    """Generate custom report based on parameters"""
    
    try:
        data = request.get_json() or {}
        
        report_type = data.get('report_type', 'users')
        date_range = data.get('date_range', '30')
        filters = data.get('filters', {})
        format_type = data.get('format', 'csv')
        
        # Generate report data
        report_data = generate_custom_report(report_type, date_range, filters)
        
        if format_type == 'csv':
            return generate_csv_response(report_data, report_type)
        elif format_type == 'pdf':
            return generate_pdf_response(report_data, report_type)
        else:
            return jsonify({"error": "Unsupported format"}), 400
    
    except Exception as e:
        logging.error(f"Report generation error: {e}")
        return jsonify({"error": str(e)}), 500

@admin_bp.route('/api/send-communication', methods=['POST'])
@login_required
@admin_required
def send_communication():
    """Send communication to users"""
    
    try:
        data = request.get_json() or {}
        
        recipient_type = data.get('recipient_type', 'single')  # single, multiple, all
        recipient_ids = data.get('recipient_ids', [])
        subject = data.get('subject', '')
        message = data.get('message', '')
        template_id = data.get('template_id')
        
        # Send communication
        result = send_user_communication(recipient_type, recipient_ids, subject, message, template_id)
        
        return jsonify(result)
    
    except Exception as e:
        logging.error(f"Communication sending error: {e}")
        return jsonify({"error": str(e), "success": False}), 500

@admin_bp.route('/api/user/<user_id>/details')
@login_required
@admin_required
def user_details(user_id):
    """Get detailed user information"""
    
    try:
        user = User.query.get_or_404(user_id)
        
        # Get user's brands and campaigns
        brands = Brand.query.filter_by(user_id=user_id).all()
        campaigns = Campaign.query.filter_by(user_id=user_id).order_by(Campaign.created_at.desc()).all()
        
        # Get user's quality checks
        quality_checks = QualityCheck.query.filter_by(user_id=user_id).order_by(QualityCheck.created_at.desc()).limit(20).all()
        
        user_data = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "subscription_tier": getattr(user, 'subscription_tier', 'FREE'),
            "created_at": user.created_at.isoformat(),
            "last_login": getattr(user, 'last_login', None),
            "brands_count": len(brands),
            "campaigns_count": len(campaigns),
            "quality_checks_count": len(quality_checks),
            "brands": [{"id": b.id, "name": b.name, "industry": b.industry} for b in brands],
            "recent_campaigns": [
                {
                    "id": c.id,
                    "title": c.title,
                    "status": c.status,
                    "quality_score": float(c.quality_score) if c.quality_score else None,
                    "created_at": c.created_at.isoformat()
                } for c in campaigns[:10]
            ],
            "quality_summary": {
                "total_checks": len(quality_checks),
                "passed_checks": len([q for q in quality_checks if q.passed]),
                "average_score": sum(float(q.quality_score) for q in quality_checks if q.quality_score) / len(quality_checks) if quality_checks else 0
            }
        }
        
        return jsonify(user_data)
    
    except Exception as e:
        logging.error(f"User details error: {e}")
        return jsonify({"error": str(e)}), 500

# Helper Functions

def get_dashboard_stats():
    """Get overview statistics for admin dashboard"""
    
    total_users = User.query.count()
    total_campaigns = Campaign.query.count()
    total_brands = Brand.query.count()
    total_quality_checks = QualityCheck.query.count()
    
    # Recent activity (last 7 days)
    week_ago = datetime.now() - timedelta(days=7)
    new_users_week = User.query.filter(User.created_at >= week_ago).count()
    new_campaigns_week = Campaign.query.filter(Campaign.created_at >= week_ago).count()
    
    # Quality metrics
    quality_pass_rate = 0
    if total_quality_checks > 0:
        passed_checks = QualityCheck.query.filter(QualityCheck.passed == True).count()
        quality_pass_rate = (passed_checks / total_quality_checks) * 100
    
    return {
        "total_users": total_users,
        "total_campaigns": total_campaigns,
        "total_brands": total_brands,
        "total_quality_checks": total_quality_checks,
        "new_users_week": new_users_week,
        "new_campaigns_week": new_campaigns_week,
        "quality_pass_rate": round(quality_pass_rate, 1)
    }

def get_recent_activity():
    """Get recent platform activity"""
    
    # Recent users
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    
    # Recent campaigns
    recent_campaigns = Campaign.query.order_by(Campaign.created_at.desc()).limit(5).all()
    
    # Recent quality checks
    recent_quality = QualityCheck.query.order_by(QualityCheck.created_at.desc()).limit(5).all()
    
    return {
        "recent_users": [
            {
                "id": u.id,
                "username": u.username,
                "email": u.email,
                "created_at": u.created_at.isoformat()
            } for u in recent_users
        ],
        "recent_campaigns": [
            {
                "id": c.id,
                "title": c.title,
                "status": c.status,
                "user_email": User.query.get(c.user_id).email if User.query.get(c.user_id) else "Unknown",
                "created_at": c.created_at.isoformat()
            } for c in recent_campaigns
        ],
        "recent_quality": [
            {
                "id": q.id,
                "campaign_id": q.campaign_id,
                "passed": q.passed,
                "quality_score": float(q.quality_score) if q.quality_score else None,
                "created_at": q.created_at.isoformat()
            } for q in recent_quality
        ]
    }

def get_quality_metrics():
    """Get quality control metrics"""
    
    total_checks = QualityCheck.query.count()
    passed_checks = QualityCheck.query.filter(QualityCheck.passed == True).count()
    failed_checks = total_checks - passed_checks
    
    # Average quality score
    avg_score_result = db.session.query(func.avg(QualityCheck.quality_score)).first()
    avg_quality_score = float(avg_score_result[0]) if avg_score_result[0] else 0
    
    # Quality trends by criteria
    criteria_averages = {}
    criteria_fields = [
        'coherent_score', 'relevant_score', 'compelling_score', 'fresh_score',
        'unique_score', 'creative_score', 'edgy_score', 'worth_paying_score'
    ]
    
    for field in criteria_fields:
        avg_result = db.session.query(func.avg(getattr(QualityCheck, field))).first()
        criteria_averages[field] = float(avg_result[0]) if avg_result[0] else 0
    
    return {
        "total_checks": total_checks,
        "passed_checks": passed_checks,
        "failed_checks": failed_checks,
        "pass_rate": (passed_checks / total_checks * 100) if total_checks > 0 else 0,
        "average_quality_score": round(avg_quality_score, 2),
        "criteria_averages": criteria_averages
    }

def get_user_metrics():
    """Get user engagement metrics"""

    # METRICS FOOTGUN: this query (and monthly_registrations / campaign_activity
    # below) counts ALL users, including is_salesperson=True and is_admin=True
    # accounts created during the internal-tool phase. Before the eventual D2C
    # relaunch, every SaaS-facing report needs `.filter(User.is_salesperson == False, User.is_admin == False)`
    # added so internal staff don't inflate customer counts or skew tier distribution.
    # See models.py User.is_salesperson definition for full context.
    # TODO(d2c-relaunch): add `User.is_salesperson == False, User.is_admin == False` filter.
    tier_distribution = db.session.query(
        User.subscription_tier,
        func.count(User.id)
    ).group_by(User.subscription_tier).all()

    # User activity by registration date.
    # Computed in Python rather than with SQL date_trunc() so it works on both
    # SQLite (local dev) and Postgres (prod) — date_trunc is Postgres-only.
    # TODO(d2c-relaunch): exclude is_salesperson/is_admin so internal-tool
    # signups don't pollute the new-customer trend line.
    monthly_counts = {}
    for (created_at,) in db.session.query(User.created_at).all():
        if not created_at:
            continue
        key = created_at.strftime('%Y-%m')
        monthly_counts[key] = monthly_counts.get(key, 0) + 1
    monthly_registrations = sorted(monthly_counts.items())[-12:]

    # Average campaigns per tier. Done as two simple queries + Python division
    # because func.avg(func.count(...)) is an invalid nested aggregate in SQL.
    # TODO(d2c-relaunch): exclude is_salesperson/is_admin accounts.
    users_per_tier = dict(
        db.session.query(User.subscription_tier, func.count(User.id))
        .group_by(User.subscription_tier).all()
    )
    campaigns_per_tier = dict(
        db.session.query(User.subscription_tier, func.count(Campaign.id))
        .join(Campaign).group_by(User.subscription_tier).all()
    )
    campaign_activity = {
        tier: round(campaigns_per_tier.get(tier, 0) / users_per_tier[tier], 2)
        for tier in users_per_tier if users_per_tier[tier]
    }

    return {
        "tier_distribution": dict(tier_distribution),
        "monthly_registrations": [
            {"month": month, "count": count}
            for month, count in monthly_registrations
        ],
        "campaign_activity": campaign_activity
    }

def generate_custom_report(report_type, date_range, filters):
    """Generate custom report data"""
    
    # Calculate date range
    end_date = datetime.now()
    if date_range == '7':
        start_date = end_date - timedelta(days=7)
    elif date_range == '30':
        start_date = end_date - timedelta(days=30)
    elif date_range == '90':
        start_date = end_date - timedelta(days=90)
    else:
        start_date = end_date - timedelta(days=365)
    
    if report_type == 'users':
        return generate_users_report(start_date, end_date, filters)
    elif report_type == 'campaigns':
        return generate_campaigns_report(start_date, end_date, filters)
    elif report_type == 'quality':
        return generate_quality_report(start_date, end_date, filters)
    else:
        return []

def generate_users_report(start_date, end_date, filters):
    """Generate users report data"""
    
    query = User.query.filter(User.created_at.between(start_date, end_date))
    
    # Apply filters
    if filters.get('subscription_tier'):
        query = query.filter(User.subscription_tier == filters['subscription_tier'])
    
    users = query.all()
    
    report_data = []
    for user in users:
        brands_count = Brand.query.filter_by(user_id=user.id).count()
        campaigns_count = Campaign.query.filter_by(user_id=user.id).count()
        
        report_data.append({
            "User ID": user.id,
            "Username": user.username,
            "Email": user.email,
            "Subscription Tier": getattr(user, 'subscription_tier', 'FREE'),
            "Brands Count": brands_count,
            "Campaigns Count": campaigns_count,
            "Registration Date": user.created_at.strftime('%Y-%m-%d %H:%M:%S')
        })
    
    return report_data

def generate_campaigns_report(start_date, end_date, filters):
    """Generate campaigns report data"""
    
    query = Campaign.query.filter(Campaign.created_at.between(start_date, end_date))
    
    # Apply filters
    if filters.get('status'):
        query = query.filter(Campaign.status == filters['status'])
    
    campaigns = query.all()
    
    report_data = []
    for campaign in campaigns:
        user = User.query.get(campaign.user_id)
        brand = Brand.query.get(campaign.brand_id)
        
        report_data.append({
            "Campaign ID": campaign.id,
            "Title": campaign.title,
            "Status": campaign.status,
            "Quality Score": float(campaign.quality_score) if campaign.quality_score else 0,
            "User Email": user.email if user else "Unknown",
            "Brand Name": brand.name if brand else "Unknown",
            "Target Audience": campaign.target_audience or "",
            "Brand Voice": campaign.brand_voice or "",
            "Created Date": campaign.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            "Completed Date": campaign.completed_at.strftime('%Y-%m-%d %H:%M:%S') if campaign.completed_at else ""
        })
    
    return report_data

def generate_quality_report(start_date, end_date, filters):
    """Generate quality control report data"""
    
    query = QualityCheck.query.filter(QualityCheck.created_at.between(start_date, end_date))
    
    # Apply filters
    if filters.get('passed') is not None:
        query = query.filter(QualityCheck.passed == filters['passed'])
    
    quality_checks = query.all()
    
    report_data = []
    for check in quality_checks:
        campaign = Campaign.query.get(check.campaign_id)
        user = User.query.get(check.user_id)
        
        report_data.append({
            "Check ID": check.id,
            "Campaign ID": check.campaign_id,
            "Campaign Title": campaign.title if campaign else "Unknown",
            "User Email": user.email if user else "Unknown",
            "Passed": check.passed,
            "Quality Score": float(check.quality_score) if check.quality_score else 0,
            "Regeneration Attempt": check.regeneration_attempt,
            "Model Used": check.model_used,
            "Coherent Score": float(check.coherent_score) if check.coherent_score else 0,
            "Relevant Score": float(check.relevant_score) if check.relevant_score else 0,
            "Compelling Score": float(check.compelling_score) if check.compelling_score else 0,
            "Fresh Score": float(check.fresh_score) if check.fresh_score else 0,
            "Unique Score": float(check.unique_score) if check.unique_score else 0,
            "Creative Score": float(check.creative_score) if check.creative_score else 0,
            "Edgy Score": float(check.edgy_score) if check.edgy_score else 0,
            "Worth Paying Score": float(check.worth_paying_score) if check.worth_paying_score else 0,
            "Check Date": check.created_at.strftime('%Y-%m-%d %H:%M:%S')
        })
    
    return report_data

def generate_csv_response(data, report_type):
    """Generate CSV response for report data"""
    
    if not data:
        return jsonify({"error": "No data to export"}), 400
    
    output = StringIO()
    
    if data:
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    
    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = f"attachment; filename={report_type}_report_{datetime.now().strftime('%Y%m%d')}.csv"
    response.headers["Content-type"] = "text/csv"
    
    return response

def generate_pdf_response(data, report_type):
    """Generate PDF response for report data (placeholder)"""
    
    # For now, return JSON with note about PDF generation
    # In production, this would use a PDF generation library like ReportLab
    return jsonify({
        "message": "PDF generation not yet implemented",
        "data_count": len(data),
        "suggested_action": "Use CSV export for now"
    })

def get_report_configuration():
    """Get available report configuration options"""
    
    return {
        "report_types": [
            {"value": "users", "label": "Users Report"},
            {"value": "campaigns", "label": "Campaigns Report"},
            {"value": "quality", "label": "Quality Control Report"},
            {"value": "engagement", "label": "User Engagement Report"}
        ],
        "date_ranges": [
            {"value": "7", "label": "Last 7 days"},
            {"value": "30", "label": "Last 30 days"},
            {"value": "90", "label": "Last 90 days"},
            {"value": "365", "label": "Last year"}
        ],
        "filters": {
            "users": [
                {"field": "subscription_tier", "label": "Subscription Tier", "type": "select", 
                 "options": ["FREE", "BASIC", "PLUS", "PRO", "ENTERPRISE"]}
            ],
            "campaigns": [
                {"field": "status", "label": "Status", "type": "select",
                 "options": ["pending", "processing", "completed", "failed", "regenerating", "human_review"]}
            ],
            "quality": [
                {"field": "passed", "label": "Quality Status", "type": "select",
                 "options": [{"value": True, "label": "Passed"}, {"value": False, "label": "Failed"}]}
            ]
        }
    }

def get_communication_templates():
    """Get predefined communication templates"""
    
    return [
        {
            "id": "welcome",
            "name": "Welcome Message",
            "subject": "Welcome to Dominate Marketing!",
            "template": "Welcome to Dominate Marketing! We're excited to help you create amazing campaigns that dominate your market."
        },
        {
            "id": "quality_improvement",
            "name": "Quality Improvement Notice",
            "subject": "Your Campaign Quality Enhancement",
            "template": "We've enhanced your campaign content to ensure it meets our premium quality standards. Your improved content is now ready!"
        },
        {
            "id": "feature_announcement",
            "name": "New Feature Announcement",
            "subject": "Exciting New Features in Dominate Marketing",
            "template": "We've added powerful new features to help you create even more effective marketing campaigns."
        }
    ]

def send_user_communication(recipient_type, recipient_ids, subject, message, template_id):
    """Send communication to users"""
    
    try:
        # Get recipients
        if recipient_type == 'all':
            recipients = User.query.all()
        elif recipient_type == 'multiple':
            recipients = User.query.filter(User.id.in_(recipient_ids)).all()
        else:  # single
            recipients = User.query.filter(User.id.in_(recipient_ids)).all()
        
        # Apply template if specified
        if template_id:
            templates = get_communication_templates()
            template = next((t for t in templates if t['id'] == template_id), None)
            if template:
                subject = template['subject']
                message = template['template']
        
        sent_count = 0
        failed_count = 0
        
        # Send to each recipient (in production, this would use a proper email service)
        for recipient in recipients:
            try:
                # Log the communication
                logging.info(f"ADMIN COMMUNICATION TO: {recipient.email}")
                logging.info(f"SUBJECT: {subject}")
                logging.info(f"MESSAGE: {message}")
                sent_count += 1
            except Exception as e:
                logging.error(f"Failed to send communication to {recipient.email}: {e}")
                failed_count += 1
        
        return {
            "success": True,
            "sent_count": sent_count,
            "failed_count": failed_count,
            "total_recipients": len(recipients)
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def get_detailed_user_stats():
    """Get detailed user statistics"""
    
    total_users = User.query.count()
    
    # Tier distribution
    tier_stats = db.session.query(
        User.subscription_tier,
        func.count(User.id)
    ).group_by(User.subscription_tier).all()
    
    # Active users (users with campaigns)
    active_users = db.session.query(User.id).join(Campaign).distinct().count()
    
    # Recent registrations
    week_ago = datetime.now() - timedelta(days=7)
    recent_registrations = User.query.filter(User.created_at >= week_ago).count()
    
    return {
        "total_users": total_users,
        "tier_distribution": dict(tier_stats),
        "active_users": active_users,
        "inactive_users": total_users - active_users,
        "recent_registrations": recent_registrations
    }

def get_quality_control_overview():
    """Get quality control overview"""
    
    total_checks = QualityCheck.query.count()
    passed_checks = QualityCheck.query.filter(QualityCheck.passed == True).count()
    
    # Human review campaigns
    human_review_campaigns = Campaign.query.filter(Campaign.status == 'human_review').count()
    
    # Average regeneration attempts
    avg_attempts = db.session.query(func.avg(QualityCheck.regeneration_attempt)).first()
    avg_regeneration_attempts = float(avg_attempts[0]) if avg_attempts[0] else 0
    
    return {
        "total_checks": total_checks,
        "passed_checks": passed_checks,
        "failed_checks": total_checks - passed_checks,
        "pass_rate": (passed_checks / total_checks * 100) if total_checks > 0 else 0,
        "human_review_campaigns": human_review_campaigns,
        "average_regeneration_attempts": round(avg_regeneration_attempts, 2)
    }

def get_quality_trends():
    """Get quality trends over time"""
    
    # Get quality trends by day for the last 30 days
    thirty_days_ago = datetime.now() - timedelta(days=30)
    
    daily_quality = db.session.query(
        func.date(QualityCheck.created_at).label('date'),
        func.count(QualityCheck.id).label('total'),
        # SQLAlchemy 2.x case(): positional when-clauses, not a list + func.case.
        func.sum(case((QualityCheck.passed == True, 1), else_=0)).label('passed')
    ).filter(
        QualityCheck.created_at >= thirty_days_ago
    ).group_by(
        func.date(QualityCheck.created_at)
    ).order_by('date').all()

    trends = []
    for date, total, passed in daily_quality:
        passed = passed or 0
        pass_rate = (passed / total * 100) if total > 0 else 0
        # func.date() returns a str on SQLite and a date on Postgres — handle both.
        date_str = date.strftime('%Y-%m-%d') if hasattr(date, 'strftime') else str(date)
        trends.append({
            "date": date_str,
            "total_checks": total,
            "passed_checks": passed,
            "pass_rate": round(pass_rate, 1)
        })

    return trends