"""
Licensing API endpoints for Dominate Marketing
Provides one-click license generation and management
"""
from flask import Blueprint, jsonify, request, render_template, make_response, session
from flask_login import login_required, current_user
from services.media_licensing import MediaLicensingGenerator
from models import db, Campaign
import logging
from datetime import datetime

licensing_api = Blueprint('licensing_api', __name__)
logger = logging.getLogger(__name__)

@licensing_api.route('/api/license/generate', methods=['POST'])
@login_required
def generate_license():
    """Generate a new license for user's content"""
    try:
        data = request.get_json()
        generator = MediaLicensingGenerator()
        
        # Get user's subscription tier (fallback to basic if not set)
        user_tier = getattr(current_user, 'subscription_tier', 'basic')
        
        content_type = data.get('content_type', 'Marketing Content')
        campaign_id = data.get('campaign_id', f'DEMO-{datetime.now().strftime("%Y%m%d")}')
        custom_terms = data.get('custom_terms', None)
        
        # Generate the license
        license_data = generator.generate_license(
            user_tier=user_tier,
            content_type=content_type,
            campaign_id=campaign_id,
            user_id=str(current_user.id),
            custom_terms=custom_terms
        )
        
        return jsonify({
            'success': True,
            'license': license_data
        })
        
    except Exception as e:
        logger.error(f"Error generating license: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to generate license'
        }), 500

@licensing_api.route('/api/license/summary/<tier>')
def get_license_summary(tier):
    """Get licensing summary for a subscription tier"""
    try:
        generator = MediaLicensingGenerator()
        summary = generator.generate_quick_license_summary(tier)
        
        return jsonify({
            'success': True,
            'summary': summary
        })
        
    except Exception as e:
        logger.error(f"Error getting license summary: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get license summary'
        }), 500

@licensing_api.route('/api/license/verify/<license_id>')
def verify_license(license_id):
    """Verify a license ID"""
    try:
        generator = MediaLicensingGenerator()
        validation = generator.validate_license(license_id)
        
        return jsonify({
            'success': True,
            'validation': validation
        })
        
    except Exception as e:
        logger.error(f"Error verifying license: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to verify license'
        }), 500

@licensing_api.route('/api/license/download/<license_id>')
def download_license(license_id):
    """Download license document as text file"""
    try:
        generator = MediaLicensingGenerator()
        validation = generator.validate_license(license_id)
        
        if not validation.get('valid'):
            return jsonify({'error': 'Invalid license ID'}), 404
        
        # For demo purposes, generate a sample license document
        # In production, this would retrieve the actual stored license
        license_data = generator.generate_license(
            user_tier='pro',  # This would be retrieved from database
            content_type='Marketing Content',
            campaign_id='SAMPLE',
            user_id='sample-user'
        )
        
        response = make_response(license_data['document'])
        response.headers['Content-Type'] = 'text/plain'
        response.headers['Content-Disposition'] = f'attachment; filename=license-{license_id}.txt'
        
        return response
        
    except Exception as e:
        logger.error(f"Error downloading license: {e}")
        return jsonify({'error': 'Failed to download license'}), 500

@licensing_api.route('/licensing')
def licensing_page():
    """Licensing information and management page"""
    return render_template('licensing/index.html')

@licensing_api.route('/licensing/demo')
def licensing_demo():
    """Demo license generation for testing"""
    try:
        generator = MediaLicensingGenerator()
        
        # Generate demo licenses for all tiers
        demo_licenses = {}
        for tier in ['basic', 'plus', 'pro', 'enterprise']:
            demo_licenses[tier] = generator.generate_quick_license_summary(tier)
        
        return render_template('licensing/demo.html', demo_licenses=demo_licenses)
        
    except Exception as e:
        logger.error(f"Error in licensing demo: {e}")
        return render_template('errors/500.html'), 500