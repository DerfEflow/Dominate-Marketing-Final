"""
API endpoints for the trend harvester system
Integrates with existing Flask application
"""

from flask import Blueprint, request, jsonify, render_template
import logging
from typing import Dict, Any
import asyncio
from concurrent.futures import ThreadPoolExecutor
import json

from services.trend_harvester import TrendHarvester

logger = logging.getLogger(__name__)

# Create blueprint for trend API
trend_api = Blueprint('trend_api', __name__, url_prefix='/api/trends')

# Global trend harvester instance
_harvester = None

def get_harvester():
    """Get or create trend harvester instance"""
    global _harvester
    if _harvester is None:
        _harvester = TrendHarvester()
    return _harvester

@trend_api.route('/analyze', methods=['POST'])
def analyze_url():
    """
    POST /api/trends/analyze
    Body: { "url": "https://example.com/products" }
    Returns: { "run_id": 123, "status": "started" }
    """
    try:
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({'error': 'URL is required'}), 400
        
        url = data['url'].strip()
        if not url:
            return jsonify({'error': 'Valid URL is required'}), 400
        
        # Validate URL format
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        harvester = get_harvester()
        
        # Start analysis in background thread
        executor = ThreadPoolExecutor(max_workers=2)
        future = executor.submit(harvester.run_analysis, url)
        
        # Get run_id immediately (this creates the run record)
        try:
            run_id = future.result(timeout=2)  # Quick timeout to get run_id
        except:
            # If we can't get run_id quickly, create a placeholder response
            return jsonify({'error': 'Failed to start analysis'}), 500
        
        return jsonify({
            'run_id': run_id,
            'status': 'started',
            'message': 'Trend analysis started. Check status with /api/trends/runs/{run_id}/status'
        })
        
    except Exception as e:
        logger.error(f"Error starting trend analysis: {e}")
        return jsonify({'error': str(e)}), 500

@trend_api.route('/runs/<int:run_id>/status', methods=['GET'])
def get_run_status(run_id: int):
    """
    GET /api/trends/runs/{run_id}/status
    Returns: { "status": "completed|running|failed", "notes": "..." }
    """
    try:
        harvester = get_harvester()
        status = harvester.get_run_status(run_id)
        
        if status['status'] == 'not_found':
            return jsonify({'error': 'Run not found'}), 404
        
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Error getting run status: {e}")
        return jsonify({'error': str(e)}), 500

@trend_api.route('/runs/<int:run_id>/results', methods=['GET'])
def get_run_results(run_id: int):
    """
    GET /api/trends/runs/{run_id}/results
    Returns comprehensive analysis results
    """
    try:
        harvester = get_harvester()
        results = harvester.get_results(run_id)
        
        if not results:
            return jsonify({'error': 'Run not found or no results available'}), 404
        
        # Transform results for API response
        response = {
            'run_info': {
                'id': results['run']['id'],
                'url': results['run']['url'],
                'status': results['run']['status'],
                'started_at': results['run']['started_at'],
                'finished_at': results['run']['finished_at']
            },
            'detected_category': {
                'name': results['run']['detected_category_name'],
                'trends_id': results['run']['detected_category_id'],
                'youtube_id': results['run']['youtube_category_id']
            },
            'keywords': results['keywords'][:10],
            'trends_interest': _group_trends_by_keyword(results['trends_interest']),
            'rising_queries': results['related_queries'][:10],
            'youtube_videos': results['youtube_videos'][:15],
            'news_articles': results['news_articles'][:25]
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error getting run results: {e}")
        return jsonify({'error': str(e)}), 500

@trend_api.route('/categories', methods=['GET'])
def get_categories():
    """
    GET /api/trends/categories
    Returns available trend categories
    """
    try:
        harvester = get_harvester()
        categories = harvester.category_resolver.CATEGORY_MAPPINGS
        
        return jsonify({
            'categories': [
                {
                    'name': name,
                    'trends_id': data['trends_id'],
                    'youtube_id': data['youtube_id']
                }
                for name, data in categories.items()
            ]
        })
        
    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        return jsonify({'error': str(e)}), 500

@trend_api.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        harvester = get_harvester()
        return jsonify({
            'status': 'healthy',
            'services': {
                'database': 'connected',
                'trends': 'available',
                'youtube_api': 'available' if harvester.youtube_api_key else 'not_configured',
                'news_api': 'available' if (harvester.serpapi_key or harvester.gnews_api_key) else 'not_configured'
            }
        })
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

def _group_trends_by_keyword(trends_data):
    """Group trends interest data by keyword for easier consumption"""
    grouped = {}
    for trend in trends_data:
        keyword = trend['keyword']
        if keyword not in grouped:
            grouped[keyword] = []
        grouped[keyword].append({
            'date': trend['date'],
            'interest': trend['interest']
        })
    return grouped

# Integration routes for main dashboard
@trend_api.route('/dashboard', methods=['GET'])
def trends_dashboard():
    """Render trends analysis dashboard"""
    return render_template('trends/dashboard.html')

@trend_api.route('/demo', methods=['GET'])
def trends_demo():
    """Demo page for trends analysis"""
    return render_template('trends/demo.html')