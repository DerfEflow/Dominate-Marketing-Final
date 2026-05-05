"""
Trends API service for Dominate Marketing
Provides real-time access to viral trends for campaign integration
"""
from flask import Blueprint, jsonify, request
from services.trends_collector import TrendsCollector
import logging

trends_api = Blueprint('trends_api', __name__)
logger = logging.getLogger(__name__)

@trends_api.route('/api/trends/current', methods=['GET'])
def get_current_trends():
    """Get current viral trends with scores"""
    try:
        collector = TrendsCollector()
        limit = int(request.args.get('limit', 10))
        industry = request.args.get('industry', None)
        
        trends = collector.get_top_viral_trends(limit)
        
        # Filter by relevance if requested
        relevance_filter = request.args.get('relevance', None)
        if relevance_filter:
            trends = [t for t in trends if t['relevance'] == relevance_filter]
        
        return jsonify({
            'success': True,
            'count': len(trends),
            'trends': trends,
            'industry_context': industry,
            'last_updated': trends[0]['created_at'] if trends else None
        })
        
    except Exception as e:
        logger.error(f"Error fetching current trends: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch trends',
            'trends': []
        }), 500

@trends_api.route('/api/trends/context', methods=['GET'])
def get_trend_context():
    """Get formatted trend context for AI content generation"""
    try:
        collector = TrendsCollector()
        industry = request.args.get('industry', None)
        
        context = collector.get_trend_context_for_ai(industry)
        
        return jsonify({
            'success': True,
            'context': context,
            'industry': industry
        })
        
    except Exception as e:
        logger.error(f"Error generating trend context: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to generate trend context',
            'context': 'No current trends available.'
        }), 500

@trends_api.route('/api/trends/health', methods=['GET'])
def trends_health_check():
    """Health check for trends service"""
    try:
        collector = TrendsCollector()
        trends = collector.get_top_viral_trends(1)
        
        return jsonify({
            'success': True,
            'service': 'trends_collector',
            'status': 'operational',
            'last_trend': trends[0] if trends else None
        })
        
    except Exception as e:
        logger.error(f"Trends health check failed: {e}")
        return jsonify({
            'success': False,
            'service': 'trends_collector',
            'status': 'error',
            'error': str(e)
        }), 500