"""
Marketing Strategy Blueprint - Main integration point for the Marketing Strategy Agent
Handles website analysis requests and provides strategy generation interface
"""

import logging
import json
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user

from services.marketing_strategy_agent import MarketingStrategyAgent
from services.strategy_data_repository import StrategyDataRepository
from services.comprehensive_strategy_generator import ComprehensiveStrategyGenerator, CampaignRequest
from models import db, Brand, Campaign, StrategyAnalysis

# Create blueprint
marketing_strategy = Blueprint('marketing_strategy', __name__, url_prefix='/strategy')

# Initialize services
strategy_agent = MarketingStrategyAgent()
data_repository = StrategyDataRepository()
comprehensive_generator = ComprehensiveStrategyGenerator()

@marketing_strategy.route('/analyze')
@login_required
def analyze_form():
    """Show website analysis form"""
    brands = Brand.query.filter_by(user_id=current_user.id, is_active=True).all()
    
    if not brands:
        flash('Please create a brand before analyzing websites.', 'warning')
        return redirect(url_for('dashboard.brands'))
    
    return render_template('marketing_strategy/analyze.html', brands=brands)

@marketing_strategy.route('/analyze', methods=['POST'])
@login_required
def submit_analysis():
    """Submit website for analysis"""
    try:
        # Get form data
        url = request.form.get('url', '').strip()
        brand_id = request.form.get('brand_id', '').strip()
        geo_location = request.form.get('geo_location', 'US').strip()
        
        if not url or not brand_id:
            flash('Website URL and brand selection are required.', 'error')
            return redirect(url_for('marketing_strategy.analyze_form'))
        
        # Verify brand ownership
        brand = Brand.query.filter_by(id=brand_id, user_id=current_user.id).first()
        if not brand:
            flash('Invalid brand selection.', 'error')
            return redirect(url_for('marketing_strategy.analyze_form'))
        
        # Start analysis
        flash(f'Starting comprehensive analysis of {url}. This may take a few minutes...', 'info')
        
        # Run analysis
        analysis_result = strategy_agent.analyze_website(url, brand_id, geo_location)
        
        # Store results
        analysis_id = data_repository.store_analysis(analysis_result, brand_id)
        
        flash(f'Analysis complete! Confidence score: {analysis_result["confidence_score"]:.1%}', 'success')
        return redirect(url_for('marketing_strategy.view_analysis', analysis_id=analysis_id))
        
    except Exception as e:
        logging.error(f"Analysis submission failed: {e}")
        flash(f'Analysis failed: {str(e)}', 'error')
        return redirect(url_for('marketing_strategy.analyze_form'))

@marketing_strategy.route('/analysis/<analysis_id>')
@login_required
def view_analysis(analysis_id):
    """View detailed analysis results"""
    try:
        # Get analysis data
        analysis_data = data_repository.get_analysis_by_campaign(analysis_id)
        
        if not analysis_data:
            flash('Analysis not found.', 'error')
            return redirect(url_for('marketing_strategy.dashboard'))
        
        # Verify ownership through brand
        brand = Brand.query.filter_by(id=analysis_data['brand_id'], user_id=current_user.id).first()
        if not brand:
            flash('Access denied.', 'error')
            return redirect(url_for('marketing_strategy.dashboard'))
        
        return render_template('marketing_strategy/analysis.html', 
                             analysis=analysis_data, 
                             brand=brand)
        
    except Exception as e:
        logging.error(f"View analysis failed: {e}")
        flash(f'Error loading analysis: {str(e)}', 'error')
        return redirect(url_for('marketing_strategy.dashboard'))

@marketing_strategy.route('/dashboard')
@login_required
def dashboard():
    """Marketing strategy dashboard with all analyses"""
    try:
        # Get user's brands
        brands = Brand.query.filter_by(user_id=current_user.id, is_active=True).all()
        
        dashboard_data = {}
        
        for brand in brands:
            # Get latest analysis
            latest_analysis = data_repository.get_latest_analysis_by_brand(brand.id)
            
            # Get trend summary
            trend_summary = data_repository.get_trend_summary(brand.id, days_back=30)
            
            # Get competitive intelligence
            competitive_intel = data_repository.get_competitive_intelligence(brand.id)
            
            # Get content strategy data
            content_strategy = data_repository.get_content_strategy_data(brand.id)
            
            dashboard_data[brand.id] = {
                'brand': brand,
                'latest_analysis': latest_analysis,
                'trend_summary': trend_summary,
                'competitive_intel': competitive_intel,
                'content_strategy': content_strategy
            }
        
        return render_template('marketing_strategy/dashboard.html', 
                             brands=brands, 
                             dashboard_data=dashboard_data)
        
    except Exception as e:
        logging.error(f"Dashboard error: {e}")
        flash(f'Error loading dashboard: {str(e)}', 'error')
        return render_template('marketing_strategy/dashboard.html', brands=[], dashboard_data={})

@marketing_strategy.route('/brand/<brand_id>/analyses')
@login_required
def brand_analyses(brand_id):
    """Show all analyses for a specific brand"""
    try:
        # Verify brand ownership
        brand = Brand.query.filter_by(id=brand_id, user_id=current_user.id).first()
        if not brand:
            flash('Brand not found.', 'error')
            return redirect(url_for('marketing_strategy.dashboard'))
        
        # Get all analyses for this brand
        analyses = StrategyAnalysis.query.filter_by(brand_id=brand_id)\
            .order_by(StrategyAnalysis.created_at.desc())\
            .limit(50).all()
        
        # Serialize for template
        serialized_analyses = []
        for analysis in analyses:
            serialized_analyses.append(data_repository._serialize_analysis(analysis))
        
        return render_template('marketing_strategy/brand_analyses.html', 
                             brand=brand, 
                             analyses=serialized_analyses)
        
    except Exception as e:
        logging.error(f"Brand analyses error: {e}")
        flash(f'Error loading analyses: {str(e)}', 'error')
        return redirect(url_for('marketing_strategy.dashboard'))

@marketing_strategy.route('/content-calendar/<brand_id>')
@login_required
def content_calendar(brand_id):
    """Generate content calendar based on analysis"""
    try:
        # Verify brand ownership
        brand = Brand.query.filter_by(id=brand_id, user_id=current_user.id).first()
        if not brand:
            flash('Brand not found.', 'error')
            return redirect(url_for('marketing_strategy.dashboard'))
        
        # Get content strategy data
        content_strategy = data_repository.get_content_strategy_data(brand_id)
        
        if not content_strategy or content_strategy.get('error'):
            flash('No content strategy data available. Please run a website analysis first.', 'warning')
            return redirect(url_for('marketing_strategy.analyze_form'))
        
        return render_template('marketing_strategy/content_calendar.html', 
                             brand=brand, 
                             content_strategy=content_strategy)
        
    except Exception as e:
        logging.error(f"Content calendar error: {e}")
        flash(f'Error loading content calendar: {str(e)}', 'error')
        return redirect(url_for('marketing_strategy.dashboard'))

@marketing_strategy.route('/competitor-analysis/<brand_id>')
@login_required
def competitor_analysis(brand_id):
    """Show competitive analysis for a brand"""
    try:
        # Verify brand ownership
        brand = Brand.query.filter_by(id=brand_id, user_id=current_user.id).first()
        if not brand:
            flash('Brand not found.', 'error')
            return redirect(url_for('marketing_strategy.dashboard'))
        
        # Get competitive intelligence
        competitive_intel = data_repository.get_competitive_intelligence(brand_id)
        
        return render_template('marketing_strategy/competitor_analysis.html', 
                             brand=brand, 
                             competitive_intel=competitive_intel)
        
    except Exception as e:
        logging.error(f"Competitor analysis error: {e}")
        flash(f'Error loading competitor analysis: {str(e)}', 'error')
        return redirect(url_for('marketing_strategy.dashboard'))

@marketing_strategy.route('/api/reanalyze', methods=['POST'])
@login_required
def api_reanalyze():
    """API endpoint to trigger re-analysis"""
    try:
        data = request.get_json()
        url = data.get('url')
        brand_id = data.get('brand_id')
        geo_location = data.get('geo_location', 'US')
        
        if not url or not brand_id:
            return jsonify({'error': 'Missing required parameters'}), 400
        
        # Verify brand ownership
        brand = Brand.query.filter_by(id=brand_id, user_id=current_user.id).first()
        if not brand:
            return jsonify({'error': 'Invalid brand'}), 403
        
        # Run analysis
        analysis_result = strategy_agent.analyze_website(url, brand_id, geo_location)
        
        # Store results
        analysis_id = data_repository.store_analysis(analysis_result, brand_id)
        
        return jsonify({
            'success': True,
            'analysis_id': analysis_id,
            'confidence_score': analysis_result['confidence_score'],
            'fallback_used': analysis_result['fallback_used']
        })
        
    except Exception as e:
        logging.error(f"API reanalyze failed: {e}")
        return jsonify({'error': str(e)}), 500

@marketing_strategy.route('/api/update-confidence', methods=['POST'])
@login_required
def api_update_confidence():
    """API endpoint to update analysis confidence score"""
    try:
        data = request.get_json()
        analysis_id = data.get('analysis_id')
        new_confidence = data.get('confidence_score')
        notes = data.get('notes', '')
        
        if not analysis_id or new_confidence is None:
            return jsonify({'error': 'Missing required parameters'}), 400
        
        # Verify ownership through brand
        analysis = StrategyAnalysis.query.get(analysis_id)
        if not analysis:
            return jsonify({'error': 'Analysis not found'}), 404
        
        brand = Brand.query.filter_by(id=analysis.brand_id, user_id=current_user.id).first()
        if not brand:
            return jsonify({'error': 'Access denied'}), 403
        
        # Update confidence
        data_repository.update_analysis_confidence(analysis_id, new_confidence, notes)
        
        return jsonify({'success': True})
        
    except Exception as e:
        logging.error(f"API update confidence failed: {e}")
        return jsonify({'error': str(e)}), 500

@marketing_strategy.route('/create-campaign')
@login_required
def create_campaign_form():
    """Show comprehensive campaign creation form"""
    brands = Brand.query.filter_by(user_id=current_user.id, is_active=True).all()
    
    if not brands:
        flash('Please create a brand before generating campaigns.', 'warning')
        return redirect(url_for('dashboard.brands'))
    
    return render_template('marketing_strategy/create_campaign.html', brands=brands)

@marketing_strategy.route('/create-campaign', methods=['POST'])
@login_required
def create_campaign():
    """Create comprehensive marketing campaign"""
    try:
        # Validate generation limits
        tier_config = current_user.get_tier_config()
        if (current_user.generations_used or 0) >= tier_config.generations_per_month:
            flash('Monthly generation limit reached. Please upgrade your subscription.', 'error')
            return redirect(url_for('payment_routes.manage_subscription'))
        
        # Get form data
        brand_id = request.form.get('brand_id', '').strip()
        product_service_url = request.form.get('product_service_url', '').strip()
        campaign_goals = request.form.getlist('campaign_goals')
        tone = request.form.get('tone', '').strip()
        target_audience = request.form.get('target_audience', '').strip()
        geo_location = request.form.get('geo_location', 'US').strip()
        budget_range = request.form.get('budget_range', '').strip()
        timeframe = request.form.get('timeframe', '30_days').strip()
        
        # Validation
        if not all([brand_id, product_service_url, tone, campaign_goals]):
            flash('Please fill in all required fields.', 'error')
            return redirect(url_for('marketing_strategy.create_campaign_form'))
        
        # Verify brand ownership
        brand = Brand.query.filter_by(id=brand_id, user_id=current_user.id).first()
        if not brand:
            flash('Invalid brand selection.', 'error')
            return redirect(url_for('marketing_strategy.create_campaign_form'))
        
        # Create campaign request
        campaign_request = CampaignRequest(
            brand_id=brand_id,
            product_service_url=product_service_url,
            target_audience=target_audience,
            campaign_goals=campaign_goals,
            tone=tone,
            geo_location=geo_location,
            subscription_tier=current_user.subscription_tier,
            budget_range=budget_range if budget_range else None,
            timeframe=timeframe
        )
        
        flash('Starting comprehensive strategy generation. This may take a few minutes...', 'info')
        
        # Generate comprehensive strategy
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            comprehensive_strategy = loop.run_until_complete(
                comprehensive_generator.generate_comprehensive_strategy(campaign_request)
            )
        finally:
            loop.close()
        
        # Store the campaign
        campaign = Campaign(
            brand_id=brand_id,
            user_id=current_user.id,
            title=f"Campaign for {brand.name}",
            business_url=product_service_url,
            target_audience=target_audience,
            campaign_goal=', '.join(campaign_goals),
            brand_voice=tone,
            campaign_type='comprehensive_strategy',
            status='completed',
            target_url=product_service_url,
            analysis_data=json.dumps(comprehensive_strategy),
            confidence_score=comprehensive_strategy.get('confidence_score', 0.85)
        )
        
        db.session.add(campaign)
        
        # Update generation count
        current_user.generations_used = (current_user.generations_used or 0) + 1
        
        db.session.commit()
        
        flash(f'Comprehensive marketing strategy generated successfully! Confidence: {comprehensive_strategy.get("confidence_score", 0.85):.1%}', 'success')
        return redirect(url_for('marketing_strategy.view_campaign', campaign_id=campaign.id))
        
    except Exception as e:
        logging.error(f"Campaign creation failed: {e}")
        flash(f'Campaign generation failed: {str(e)}', 'error')
        return redirect(url_for('marketing_strategy.create_campaign_form'))

@marketing_strategy.route('/campaign/<campaign_id>')
@login_required
def view_campaign(campaign_id):
    """View comprehensive campaign results"""
    try:
        # Get campaign
        campaign = Campaign.query.filter_by(id=campaign_id, user_id=current_user.id).first()
        
        if not campaign:
            flash('Campaign not found.', 'error')
            return redirect(url_for('marketing_strategy.dashboard'))
        
        # Parse strategy data
        strategy_data = json.loads(campaign.analysis_data) if campaign.analysis_data else {}
        
        # Get brand info
        brand = Brand.query.get(campaign.brand_id)
        
        return render_template('marketing_strategy/campaign_results.html', 
                             campaign=campaign, 
                             strategy=strategy_data, 
                             brand=brand)
        
    except Exception as e:
        logging.error(f"View campaign failed: {e}")
        flash(f'Error loading campaign: {str(e)}', 'error')
        return redirect(url_for('marketing_strategy.dashboard'))

@marketing_strategy.route('/export/<brand_id>')
@login_required
def export_strategy(brand_id):
    """Export strategy data as JSON"""
    try:
        # Verify brand ownership
        brand = Brand.query.filter_by(id=brand_id, user_id=current_user.id).first()
        if not brand:
            flash('Brand not found.', 'error')
            return redirect(url_for('marketing_strategy.dashboard'))
        
        # Get comprehensive data
        export_data = {
            'brand': {
                'id': brand.id,
                'name': brand.name,
                'website_url': brand.website_url,
                'industry': brand.industry
            },
            'latest_analysis': data_repository.get_latest_analysis_by_brand(brand_id),
            'trend_summary': data_repository.get_trend_summary(brand_id, days_back=30),
            'competitive_intel': data_repository.get_competitive_intelligence(brand_id),
            'content_strategy': data_repository.get_content_strategy_data(brand_id),
            'export_timestamp': datetime.utcnow().isoformat()
        }
        
        return jsonify(export_data)
        
    except Exception as e:
        logging.error(f"Export strategy failed: {e}")
        return jsonify({'error': str(e)}), 500