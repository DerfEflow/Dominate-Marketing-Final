"""
Sell Profile API Endpoints - RESTful API for the new Sell Profile → Viral Tools system
Replaces the old trends/categories approach with intelligent business analysis
"""

from flask import Blueprint, request, jsonify
import logging
from datetime import datetime
from typing import Dict, Any
import uuid

from .sell_profile_analyzer import SellProfileAnalyzer
from .viral_tools_researcher import ViralToolsResearcher

logger = logging.getLogger(__name__)

# Create Blueprint
sell_profile_api = Blueprint('sell_profile_api', __name__, url_prefix='/api/sell-profile')

# Initialize services
profile_analyzer = SellProfileAnalyzer()
viral_researcher = ViralToolsResearcher()

# In-memory storage for demo (would be database in production)
analysis_cache = {}

@sell_profile_api.route('/analyze', methods=['POST'])
def analyze_business():
    """
    Extract comprehensive business Sell Profile and research Viral Tools
    
    POST /api/sell-profile/analyze
    Body: {"url": "https://business-website.com"}
    
    Returns: {
        "analysis_id": "uuid",
        "status": "completed",
        "sell_profile": {...},
        "viral_tools": {...}
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'url' not in data:
            return jsonify({
                'success': False,
                'error': 'URL is required in request body'
            }), 400
        
        url = data['url'].strip()
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        analysis_id = str(uuid.uuid4())
        
        logger.info(f"Starting Sell Profile analysis for {url} (ID: {analysis_id})")
        
        # Step 1: Extract Sell Profile
        sell_profile = profile_analyzer.analyze_website(url)
        
        # Step 2: Research Viral Tools based on Sell Profile
        profile_dict = profile_analyzer.export_profile(sell_profile)
        viral_tools = viral_researcher.research_viral_tools(profile_dict)
        
        # Cache results
        analysis_cache[analysis_id] = {
            'status': 'completed',
            'sell_profile': profile_dict,
            'viral_tools': viral_researcher.export_research(viral_tools),
            'created_at': datetime.now().isoformat(),
            'url': url
        }
        
        logger.info(f"Sell Profile analysis completed for {analysis_id}")
        
        return jsonify({
            'success': True,
            'analysis_id': analysis_id,
            'status': 'completed',
            'sell_profile': profile_dict,
            'viral_tools': viral_researcher.export_research(viral_tools)
        })
        
    except Exception as e:
        logger.error(f"Error in sell profile analysis: {e}")
        return jsonify({
            'success': False,
            'error': f'Analysis failed: {str(e)}'
        }), 500

@sell_profile_api.route('/analysis/<analysis_id>', methods=['GET'])
def get_analysis_results(analysis_id: str):
    """
    Get complete analysis results by ID
    
    GET /api/sell-profile/analysis/{analysis_id}
    
    Returns: {
        "analysis_id": "uuid",
        "status": "completed",
        "sell_profile": {...},
        "viral_tools": {...}
    }
    """
    try:
        if analysis_id not in analysis_cache:
            return jsonify({
                'success': False,
                'error': 'Analysis not found'
            }), 404
        
        results = analysis_cache[analysis_id]
        
        return jsonify({
            'success': True,
            'analysis_id': analysis_id,
            **results
        })
        
    except Exception as e:
        logger.error(f"Error retrieving analysis {analysis_id}: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to retrieve analysis: {str(e)}'
        }), 500

@sell_profile_api.route('/analysis/<analysis_id>/sell-profile', methods=['GET'])
def get_sell_profile(analysis_id: str):
    """
    Get only the Sell Profile portion of analysis
    
    GET /api/sell-profile/analysis/{analysis_id}/sell-profile
    """
    try:
        if analysis_id not in analysis_cache:
            return jsonify({
                'success': False,
                'error': 'Analysis not found'
            }), 404
        
        results = analysis_cache[analysis_id]
        
        return jsonify({
            'success': True,
            'analysis_id': analysis_id,
            'sell_profile': results['sell_profile']
        })
        
    except Exception as e:
        logger.error(f"Error retrieving sell profile {analysis_id}: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to retrieve sell profile: {str(e)}'
        }), 500

@sell_profile_api.route('/analysis/<analysis_id>/viral-tools', methods=['GET'])
def get_viral_tools(analysis_id: str):
    """
    Get only the Viral Tools portion of analysis
    
    GET /api/sell-profile/analysis/{analysis_id}/viral-tools
    """
    try:
        if analysis_id not in analysis_cache:
            return jsonify({
                'success': False,
                'error': 'Analysis not found'
            }), 404
        
        results = analysis_cache[analysis_id]
        
        return jsonify({
            'success': True,
            'analysis_id': analysis_id,
            'viral_tools': results['viral_tools']
        })
        
    except Exception as e:
        logger.error(f"Error retrieving viral tools {analysis_id}: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to retrieve viral tools: {str(e)}'
        }), 500

@sell_profile_api.route('/analysis/<analysis_id>/viral-tools/<tool_type>', methods=['GET'])
def get_viral_tools_by_type(analysis_id: str, tool_type: str):
    """
    Get specific type of viral tools (industry_trends, popular_viral_trends, viral_memes)
    
    GET /api/sell-profile/analysis/{analysis_id}/viral-tools/{tool_type}
    """
    try:
        if analysis_id not in analysis_cache:
            return jsonify({
                'success': False,
                'error': 'Analysis not found'
            }), 404
        
        valid_types = ['industry_trends', 'popular_viral_trends', 'viral_memes']
        if tool_type not in valid_types:
            return jsonify({
                'success': False,
                'error': f'Invalid tool type. Must be one of: {valid_types}'
            }), 400
        
        results = analysis_cache[analysis_id]
        viral_tools = results['viral_tools']
        
        return jsonify({
            'success': True,
            'analysis_id': analysis_id,
            'tool_type': tool_type,
            'viral_tools': viral_tools.get(tool_type, [])
        })
        
    except Exception as e:
        logger.error(f"Error retrieving viral tools type {tool_type} for {analysis_id}: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to retrieve viral tools: {str(e)}'
        }), 500

@sell_profile_api.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint
    
    GET /api/sell-profile/health
    """
    return jsonify({
        'success': True,
        'service': 'Sell Profile & Viral Tools API',
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'cached_analyses': len(analysis_cache)
    })

@sell_profile_api.route('/industries', methods=['GET'])
def get_supported_industries():
    """
    Get list of supported industries for classification
    
    GET /api/sell-profile/industries
    """
    industries = [
        'construction', 'healthcare', 'legal', 'automotive', 'restaurant',
        'retail', 'technology', 'real_estate', 'finance', 'beauty',
        'fitness', 'education', 'professional_services'
    ]
    
    return jsonify({
        'success': True,
        'industries': industries,
        'count': len(industries)
    })

@sell_profile_api.route('/viral-tool-types', methods=['GET'])
def get_viral_tool_types():
    """
    Get information about viral tool types and priorities
    
    GET /api/sell-profile/viral-tool-types
    """
    tool_types = {
        'industry_trends': {
            'priority': 1,
            'description': 'Industry-specific viral trends tailored to business sector',
            'content_types': ['text', 'video', 'image'],
            'platforms': ['facebook', 'instagram', 'linkedin', 'twitter']
        },
        'popular_viral_trends': {
            'priority': 2,
            'description': 'Popular viral trends not necessarily industry-specific',
            'content_types': ['video', 'image', 'text', 'mixed'],
            'platforms': ['tiktok', 'instagram', 'twitter', 'facebook']
        },
        'viral_memes': {
            'priority': 3,
            'description': 'Viral meme formats for highlighting products/services',
            'content_types': ['image', 'video'],
            'platforms': ['instagram', 'facebook', 'twitter', 'tiktok']
        }
    }
    
    return jsonify({
        'success': True,
        'viral_tool_types': tool_types,
        'methodology': 'Priority-based viral content discovery for campaign creation'
    })

# Error handlers
@sell_profile_api.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404

@sell_profile_api.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        'success': False,
        'error': 'Method not allowed'
    }), 405

@sell_profile_api.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500