"""
Quality Control API Endpoints
Provides REST API for quality control integration
"""
import json
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user

from services.quality_integration import (
    process_campaign_quality,
    trigger_content_regeneration,
    get_campaign_quality_status
)
from models import db, Campaign, QualityCheck, User

quality_api = Blueprint('quality_api', __name__, url_prefix='/api/quality')

@quality_api.route('/assess/<campaign_id>', methods=['POST'])
@login_required
def assess_campaign_quality_endpoint(campaign_id):
    """
    Assess campaign content quality using GPT-5-mini
    
    POST /api/quality/assess/<campaign_id>
    """
    
    try:
        # Verify user owns the campaign
        campaign = Campaign.query.filter_by(id=campaign_id, user_id=current_user.id).first()
        if not campaign:
            return jsonify({
                "error": "Campaign not found or access denied",
                "success": False
            }), 404
        
        # Process campaign through quality control
        result = process_campaign_quality(campaign_id)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    except Exception as e:
        logging.error(f"Quality assessment API error: {e}")
        return jsonify({
            "error": "Quality assessment failed",
            "success": False,
            "details": str(e)
        }), 500

@quality_api.route('/regenerate/<campaign_id>', methods=['POST'])
@login_required
def regenerate_content_endpoint(campaign_id):
    """
    Trigger content regeneration based on quality feedback
    
    POST /api/quality/regenerate/<campaign_id>
    Body: {"guidance": [...regeneration guidance...]}
    """
    
    try:
        # Verify user owns the campaign
        campaign = Campaign.query.filter_by(id=campaign_id, user_id=current_user.id).first()
        if not campaign:
            return jsonify({
                "error": "Campaign not found or access denied",
                "success": False
            }), 404
        
        # Get regeneration guidance from request
        data = request.get_json() or {}
        guidance = data.get('guidance', [])
        
        # Trigger regeneration
        result = trigger_content_regeneration(campaign_id, guidance)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    except Exception as e:
        logging.error(f"Content regeneration API error: {e}")
        return jsonify({
            "error": "Content regeneration failed",
            "success": False,
            "details": str(e)
        }), 500

@quality_api.route('/status/<campaign_id>', methods=['GET'])
@login_required
def get_quality_status_endpoint(campaign_id):
    """
    Get quality control status for a campaign
    
    GET /api/quality/status/<campaign_id>
    """
    
    try:
        # Verify user owns the campaign
        campaign = Campaign.query.filter_by(id=campaign_id, user_id=current_user.id).first()
        if not campaign:
            return jsonify({
                "error": "Campaign not found or access denied"
            }), 404
        
        # Get quality status
        result = get_campaign_quality_status(campaign_id)
        
        if 'error' in result:
            return jsonify(result), 400
        else:
            return jsonify(result), 200
    
    except Exception as e:
        logging.error(f"Quality status API error: {e}")
        return jsonify({
            "error": "Failed to get quality status",
            "details": str(e)
        }), 500

@quality_api.route('/history/<campaign_id>', methods=['GET'])
@login_required
def get_quality_history_endpoint(campaign_id):
    """
    Get complete quality check history for a campaign
    
    GET /api/quality/history/<campaign_id>
    """
    
    try:
        # Verify user owns the campaign
        campaign = Campaign.query.filter_by(id=campaign_id, user_id=current_user.id).first()
        if not campaign:
            return jsonify({
                "error": "Campaign not found or access denied"
            }), 404
        
        # Get all quality checks for this campaign
        quality_checks = QualityCheck.query.filter_by(campaign_id=campaign_id).order_by(QualityCheck.created_at).all()
        
        history = []
        for check in quality_checks:
            check_data = {
                "id": check.id,
                "passed": check.passed,
                "quality_score": float(check.quality_score) if check.quality_score else None,
                "regeneration_attempt": check.regeneration_attempt,
                "model_used": check.model_used,
                "created_at": check.created_at.isoformat(),
                "criteria_scores": {}
            }
            
            # Add individual criteria scores if available
            if check.coherent_score:
                check_data["criteria_scores"] = {
                    "coherent": float(check.coherent_score),
                    "relevant": float(check.relevant_score) if check.relevant_score else None,
                    "compelling": float(check.compelling_score) if check.compelling_score else None,
                    "fresh": float(check.fresh_score) if check.fresh_score else None,
                    "unique": float(check.unique_score) if check.unique_score else None,
                    "creative": float(check.creative_score) if check.creative_score else None,
                    "edgy": float(check.edgy_score) if check.edgy_score else None,
                    "worth_paying_for": float(check.worth_paying_score) if check.worth_paying_score else None
                }
            
            # Add detailed results if available
            if check.check_results:
                try:
                    detailed_results = json.loads(check.check_results)
                    check_data["detailed_results"] = detailed_results
                except:
                    pass
            
            history.append(check_data)
        
        return jsonify({
            "campaign_id": campaign_id,
            "total_checks": len(history),
            "quality_history": history,
            "current_status": campaign.status
        }), 200
    
    except Exception as e:
        logging.error(f"Quality history API error: {e}")
        return jsonify({
            "error": "Failed to get quality history",
            "details": str(e)
        }), 500

@quality_api.route('/summary', methods=['GET'])
@login_required
def get_user_quality_summary():
    """
    Get quality control summary for current user's campaigns
    
    GET /api/quality/summary
    """
    
    try:
        # Get user's campaigns and quality checks
        user_campaigns = Campaign.query.filter_by(user_id=current_user.id).all()
        user_quality_checks = QualityCheck.query.filter_by(user_id=current_user.id).all()
        
        # Calculate summary statistics
        total_campaigns = len(user_campaigns)
        total_quality_checks = len(user_quality_checks)
        
        passed_checks = len([check for check in user_quality_checks if check.passed])
        failed_checks = total_quality_checks - passed_checks
        
        # Calculate average quality scores
        quality_scores = [float(check.quality_score) for check in user_quality_checks if check.quality_score]
        avg_quality_score = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        # Status breakdown
        status_counts = {}
        for campaign in user_campaigns:
            status = campaign.status
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Recent quality trends (last 30 days)
        from datetime import timedelta
        recent_date = datetime.now() - timedelta(days=30)
        recent_checks = [check for check in user_quality_checks if check.created_at >= recent_date]
        
        recent_passed = len([check for check in recent_checks if check.passed])
        recent_total = len(recent_checks)
        recent_pass_rate = (recent_passed / recent_total * 100) if recent_total > 0 else 0
        
        summary = {
            "user_id": current_user.id,
            "total_campaigns": total_campaigns,
            "total_quality_checks": total_quality_checks,
            "passed_checks": passed_checks,
            "failed_checks": failed_checks,
            "pass_rate": (passed_checks / total_quality_checks * 100) if total_quality_checks > 0 else 0,
            "average_quality_score": round(avg_quality_score, 2),
            "campaign_status_breakdown": status_counts,
            "recent_trends": {
                "checks_last_30_days": recent_total,
                "recent_pass_rate": round(recent_pass_rate, 1)
            },
            "generated_at": datetime.now().isoformat()
        }
        
        return jsonify(summary), 200
    
    except Exception as e:
        logging.error(f"Quality summary API error: {e}")
        return jsonify({
            "error": "Failed to generate quality summary",
            "details": str(e)
        }), 500

@quality_api.route('/test', methods=['POST'])
@login_required
def test_quality_control():
    """
    Test endpoint for quality control system
    
    POST /api/quality/test
    Body: {"content": "content to test", "content_type": "text", "brand_context": {...}}
    """
    
    try:
        data = request.get_json() or {}
        
        content = data.get('content', '')
        content_type = data.get('content_type', 'text')
        brand_context = data.get('brand_context', {})
        
        if not content:
            return jsonify({
                "error": "Content is required for testing",
                "success": False
            }), 400
        
        # Import and test quality control directly
        from services.quality_control import QualityControlAgent
        
        agent = QualityControlAgent()
        assessment = agent.assess_content_quality(content, content_type, brand_context)
        
        return jsonify({
            "success": True,
            "test_results": assessment,
            "content_tested": content[:100] + "..." if len(content) > 100 else content,
            "tested_at": datetime.now().isoformat()
        }), 200
    
    except Exception as e:
        logging.error(f"Quality control test error: {e}")
        return jsonify({
            "error": "Quality control test failed",
            "success": False,
            "details": str(e)
        }), 500