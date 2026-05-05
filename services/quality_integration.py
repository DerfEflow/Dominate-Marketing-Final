"""
Quality Control Integration with Campaign Generation Pipeline
Integrates quality assessment into the content generation workflow
"""
import json
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Optional

from services.quality_control import assess_campaign_quality, handle_quality_failure
from services.admin_notifications import notify_quality_failure
from models import db, Campaign, QualityCheck, User, Brand

class QualityIntegrationService:
    """
    Service to integrate quality control into the campaign generation pipeline
    """
    
    def __init__(self):
        self.max_regenerations = 5
        
    def process_campaign_with_quality_control(self, campaign_id: str) -> Dict:
        """
        Main function to process a campaign through quality control
        
        Args:
            campaign_id: Campaign identifier
            
        Returns:
            Processing results with quality status
        """
        
        try:
            # Get campaign and related data
            campaign = Campaign.query.get(campaign_id)
            if not campaign:
                return {"error": "Campaign not found", "success": False}
            
            brand = Brand.query.get(campaign.brand_id)
            user = User.query.get(campaign.user_id)
            
            if not brand or not user:
                return {"error": "Missing brand or user data", "success": False}
            
            # Parse campaign content
            content_data = json.loads(campaign.ai_content) if campaign.ai_content else {}
            if not content_data:
                return {"error": "No content to assess", "success": False}
            
            # Prepare brand context for quality assessment
            brand_context = {
                "name": brand.name,
                "industry": brand.industry,
                "brand_voice": campaign.brand_voice,
                "target_audience": campaign.target_audience,
                "campaign_goal": campaign.campaign_goal
            }
            
            # Check existing quality checks
            existing_checks = QualityCheck.query.filter_by(campaign_id=campaign_id).count()
            
            # Assess content quality
            quality_results = assess_campaign_quality(campaign_id, content_data, brand_context)
            
            # Save quality check record
            quality_check = QualityCheck(
                campaign_id=campaign_id,
                user_id=campaign.user_id,
                check_results=json.dumps(quality_results),
                passed=quality_results.get('overall_pass', False),
                regeneration_attempt=existing_checks + 1,
                quality_score=quality_results.get('quality_summary', {}).get('average_score', 0)
            )
            db.session.add(quality_check)
            
            # Handle quality results
            if quality_results.get('overall_pass', False):
                # Content passed quality control
                campaign.status = 'completed'
                campaign.quality_score = quality_results.get('quality_summary', {}).get('average_score', 0)
                campaign.completed_at = datetime.now()
                
                db.session.commit()
                
                return {
                    "success": True,
                    "status": "passed",
                    "quality_score": campaign.quality_score,
                    "message": "Content passed quality control",
                    "ready_for_delivery": True
                }
            
            else:
                # Content failed quality control
                failure_response = handle_quality_failure(
                    campaign_id, 
                    quality_results, 
                    existing_checks + 1
                )
                
                if failure_response.get('regenerate', False):
                    # Mark for regeneration
                    campaign.status = 'regenerating'
                    db.session.commit()
                    
                    return {
                        "success": True,
                        "status": "regeneration_needed",
                        "regeneration_attempt": existing_checks + 1,
                        "guidance": failure_response.get('regeneration_guidance', []),
                        "message": f"Content requires regeneration (attempt {existing_checks + 1}/5)"
                    }
                
                else:
                    # Escalate to human intervention
                    campaign.status = 'human_review'
                    db.session.commit()
                    
                    # Send admin notification
                    campaign_data = {
                        "title": campaign.title,
                        "brand_name": brand.name,
                        "industry": brand.industry,
                        "target_audience": campaign.target_audience,
                        "brand_voice": campaign.brand_voice,
                        "campaign_goal": campaign.campaign_goal
                    }
                    
                    # Notify administrators
                    notify_quality_failure(failure_response.get('failure_report', {}), campaign_data)
                    
                    # Update user with human review message
                    user_message = failure_response.get('user_message', 
                        "Content requires additional refinement by our design team.")
                    
                    return {
                        "success": True,
                        "status": "human_review_required",
                        "regeneration_attempts": existing_checks + 1,
                        "user_message": user_message,
                        "admin_notified": True,
                        "message": "Content escalated to live design team"
                    }
        
        except Exception as e:
            logging.error(f"Quality control processing failed for campaign {campaign_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Quality control processing failed"
            }
    
    def regenerate_failed_content(self, campaign_id: str, regeneration_guidance: List[Dict]) -> Dict:
        """
        Trigger content regeneration based on quality feedback
        
        Args:
            campaign_id: Campaign identifier
            regeneration_guidance: Specific guidance for content improvement
            
        Returns:
            Regeneration status and next steps
        """
        
        try:
            campaign = Campaign.query.get(campaign_id)
            if not campaign:
                return {"error": "Campaign not found", "success": False}
            
            # Update campaign status
            campaign.status = 'regenerating'
            
            # Store regeneration guidance
            guidance_data = {
                "regeneration_guidance": regeneration_guidance,
                "regeneration_timestamp": datetime.now().isoformat(),
                "regeneration_reason": "quality_control_failure"
            }
            
            # This would integrate with your content generation system
            # For now, we'll mark it as ready for regeneration
            campaign.regeneration_data = json.dumps(guidance_data)
            
            db.session.commit()
            
            return {
                "success": True,
                "status": "regeneration_queued",
                "message": "Content regeneration initiated with quality guidance"
            }
            
        except Exception as e:
            logging.error(f"Content regeneration failed for campaign {campaign_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Content regeneration failed"
            }
    
    def get_quality_status(self, campaign_id: str) -> Dict:
        """
        Get current quality control status for a campaign
        
        Args:
            campaign_id: Campaign identifier
            
        Returns:
            Current quality status and history
        """
        
        try:
            campaign = Campaign.query.get(campaign_id)
            quality_checks = QualityCheck.query.filter_by(campaign_id=campaign_id).all()
            
            if not campaign:
                return {"error": "Campaign not found"}
            
            latest_check = quality_checks[-1] if quality_checks else None
            
            status_info = {
                "campaign_id": campaign_id,
                "current_status": campaign.status,
                "quality_score": campaign.quality_score,
                "total_quality_checks": len(quality_checks),
                "latest_check": None,
                "regeneration_attempts": len(quality_checks),
                "max_regenerations": self.max_regenerations,
                "can_regenerate": len(quality_checks) < self.max_regenerations
            }
            
            if latest_check:
                status_info["latest_check"] = {
                    "passed": latest_check.passed,
                    "quality_score": latest_check.quality_score,
                    "checked_at": latest_check.created_at.isoformat(),
                    "attempt_number": latest_check.regeneration_attempt
                }
            
            return status_info
            
        except Exception as e:
            logging.error(f"Failed to get quality status for campaign {campaign_id}: {e}")
            return {"error": str(e)}

# Integration API Functions
def process_campaign_quality(campaign_id: str) -> Dict:
    """
    Main API function to process campaign through quality control
    
    Args:
        campaign_id: Campaign identifier
        
    Returns:
        Quality processing results
    """
    service = QualityIntegrationService()
    return service.process_campaign_with_quality_control(campaign_id)

def trigger_content_regeneration(campaign_id: str, guidance: List[Dict]) -> Dict:
    """
    API function to trigger content regeneration
    
    Args:
        campaign_id: Campaign identifier
        guidance: Regeneration guidance from quality control
        
    Returns:
        Regeneration status
    """
    service = QualityIntegrationService()
    return service.regenerate_failed_content(campaign_id, guidance)

def get_campaign_quality_status(campaign_id: str) -> Dict:
    """
    API function to get campaign quality status
    
    Args:
        campaign_id: Campaign identifier
        
    Returns:
        Quality status information
    """
    service = QualityIntegrationService()
    return service.get_quality_status(campaign_id)