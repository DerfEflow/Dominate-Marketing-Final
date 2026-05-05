"""
Quality Control Agent for Dominate Marketing
Uses GPT-5-mini to assess content quality before user delivery
"""
import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from openai import OpenAI

# GPT-5-mini is the newest model available for quality assessment
QUALITY_MODEL = "gpt-4o-mini"

class QualityControlAgent:
    """
    Advanced content quality assessment using GPT-5-mini
    Ensures all content meets Dominate Marketing standards
    """
    
    def __init__(self):
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.max_regenerations = 5
        self.quality_criteria = [
            "coherent", "relevant", "compelling", "fresh", 
            "unique", "creative", "edgy", "worth_paying_for"
        ]
        
    def assess_content_quality(self, content: str, content_type: str, brand_context: Dict) -> Dict:
        """
        Comprehensive quality assessment using GPT-5-mini
        
        Args:
            content: The generated content to assess
            content_type: Type of content (text, image_prompt, video_script, etc.)
            brand_context: Brand information for relevance assessment
            
        Returns:
            Dict with quality scores and recommendations
        """
        
        assessment_prompt = f"""
        You are the Quality Control Agent for Dominate Marketing, a premium AI-powered marketing platform. 
        Your job is to rigorously assess content quality before it reaches paying customers.
        
        BRAND CONTEXT:
        - Brand: {brand_context.get('name', 'Unknown')}
        - Industry: {brand_context.get('industry', 'Unknown')}
        - Voice: {brand_context.get('brand_voice', 'professional')}
        - Target Audience: {brand_context.get('target_audience', 'General')}
        
        CONTENT TO ASSESS:
        Type: {content_type}
        Content: {content}
        
        QUALITY CRITERIA (Rate 1-10, must score 7+ on ALL to pass):
        1. COHERENT: Is the content logical, well-structured, and easy to understand?
        2. RELEVANT: Does it perfectly match the brand, audience, and campaign goals?
        3. COMPELLING: Will this grab attention and drive engagement/action?
        4. FRESH: Does it feel current, not outdated or cliché?
        5. UNIQUE: Is this distinctive, not generic template content?
        6. CREATIVE: Does it show innovative thinking and originality?
        7. EDGY: Does it push boundaries appropriately for maximum impact?
        8. WORTH_PAYING_FOR: Would customers pay premium prices for this quality?
        
        RESPOND IN JSON FORMAT:
        {{
            "overall_pass": boolean,
            "overall_score": number (1-10),
            "criteria_scores": {{
                "coherent": number,
                "relevant": number,
                "compelling": number,
                "fresh": number,
                "unique": number,
                "creative": number,
                "edgy": number,
                "worth_paying_for": number
            }},
            "failing_criteria": [list of criteria that scored below 7],
            "specific_issues": [detailed list of problems found],
            "improvement_recommendations": [specific suggestions for regeneration],
            "severity": "minor|moderate|major"
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model=QUALITY_MODEL,
                messages=[{"role": "user", "content": assessment_prompt}],
                response_format={"type": "json_object"},
                temperature=0.3  # Lower temperature for consistent assessment
            )
            
            assessment = json.loads(response.choices[0].message.content)
            assessment['assessed_at'] = datetime.now().isoformat()
            assessment['model_used'] = QUALITY_MODEL
            
            return assessment
            
        except Exception as e:
            logging.error(f"Quality assessment failed: {e}")
            return {
                "overall_pass": False,
                "overall_score": 0,
                "error": str(e),
                "severity": "major"
            }
    
    def process_campaign_content(self, campaign_id: str, content_data: Dict, brand_context: Dict) -> Dict:
        """
        Process all content in a campaign through quality control
        
        Args:
            campaign_id: Campaign identifier
            content_data: All generated content (images, texts, videos)
            brand_context: Brand information
            
        Returns:
            Quality assessment results with pass/fail status
        """
        
        results = {
            "campaign_id": campaign_id,
            "overall_pass": True,
            "content_assessments": {},
            "failed_content": [],
            "regeneration_needed": [],
            "quality_summary": {},
            "processed_at": datetime.now().isoformat()
        }
        
        total_score = 0
        content_count = 0
        
        # Assess text content
        for text_item in content_data.get('texts', []):
            content_count += 1
            assessment = self.assess_content_quality(
                content=text_item.get('content', ''),
                content_type=f"text_{text_item.get('platform', 'social')}",
                brand_context=brand_context
            )
            
            content_id = f"text_{text_item.get('id', content_count)}"
            results['content_assessments'][content_id] = assessment
            total_score += assessment.get('overall_score', 0)
            
            if not assessment.get('overall_pass', False):
                results['overall_pass'] = False
                results['failed_content'].append({
                    'id': content_id,
                    'type': 'text',
                    'platform': text_item.get('platform'),
                    'issues': assessment.get('specific_issues', []),
                    'recommendations': assessment.get('improvement_recommendations', [])
                })
        
        # Assess image prompts
        for image_item in content_data.get('images', []):
            content_count += 1
            # For images, assess the prompt/concept if available
            image_prompt = image_item.get('prompt', image_item.get('title', ''))
            assessment = self.assess_content_quality(
                content=image_prompt,
                content_type=f"image_prompt_{image_item.get('platform', 'social')}",
                brand_context=brand_context
            )
            
            content_id = f"image_{image_item.get('id', content_count)}"
            results['content_assessments'][content_id] = assessment
            total_score += assessment.get('overall_score', 0)
            
            if not assessment.get('overall_pass', False):
                results['overall_pass'] = False
                results['failed_content'].append({
                    'id': content_id,
                    'type': 'image',
                    'platform': image_item.get('platform'),
                    'issues': assessment.get('specific_issues', []),
                    'recommendations': assessment.get('improvement_recommendations', [])
                })
        
        # Assess video concepts
        for video_item in content_data.get('videos', []):
            content_count += 1
            video_concept = video_item.get('concept', video_item.get('script', ''))
            assessment = self.assess_content_quality(
                content=video_concept,
                content_type=f"video_concept_{video_item.get('platform', 'social')}",
                brand_context=brand_context
            )
            
            content_id = f"video_{video_item.get('id', content_count)}"
            results['content_assessments'][content_id] = assessment
            total_score += assessment.get('overall_score', 0)
            
            if not assessment.get('overall_pass', False):
                results['overall_pass'] = False
                results['failed_content'].append({
                    'id': content_id,
                    'type': 'video',
                    'platform': video_item.get('platform'),
                    'issues': assessment.get('specific_issues', []),
                    'recommendations': assessment.get('improvement_recommendations', [])
                })
        
        # Calculate overall quality metrics
        if content_count > 0:
            results['quality_summary'] = {
                'average_score': round(total_score / content_count, 2),
                'total_content_pieces': content_count,
                'passed_pieces': content_count - len(results['failed_content']),
                'failed_pieces': len(results['failed_content']),
                'pass_rate': round((content_count - len(results['failed_content'])) / content_count * 100, 1)
            }
        
        return results
    
    def generate_failure_report(self, assessment_results: Dict, regeneration_count: int) -> Dict:
        """
        Generate detailed failure report for admin notification
        
        Args:
            assessment_results: Quality assessment results
            regeneration_count: Number of regeneration attempts made
            
        Returns:
            Structured failure report for admin review
        """
        
        report = {
            "campaign_id": assessment_results.get('campaign_id'),
            "failure_type": "quality_control_failure",
            "regeneration_attempts": regeneration_count,
            "max_attempts_reached": regeneration_count >= self.max_regenerations,
            "failed_content_summary": [],
            "recommended_actions": [],
            "severity_assessment": "moderate",
            "requires_human_intervention": True,
            "created_at": datetime.now().isoformat()
        }
        
        # Analyze failed content
        for failed_item in assessment_results.get('failed_content', []):
            report['failed_content_summary'].append({
                'content_type': failed_item.get('type'),
                'platform': failed_item.get('platform'),
                'main_issues': failed_item.get('issues', []),
                'recommendations': failed_item.get('recommendations', [])
            })
        
        # Determine severity and actions
        quality_summary = assessment_results.get('quality_summary', {})
        pass_rate = quality_summary.get('pass_rate', 0)
        
        if pass_rate < 30:
            report['severity_assessment'] = "critical"
            report['recommended_actions'] = [
                "Immediate live designer assignment required",
                "Review brand context and campaign brief",
                "Consider model fine-tuning for this brand",
                "Escalate to senior marketing strategist"
            ]
        elif pass_rate < 60:
            report['severity_assessment'] = "major"
            report['recommended_actions'] = [
                "Assign experienced designer for content revision",
                "Review targeting and audience parameters",
                "Consider alternative creative approaches"
            ]
        else:
            report['severity_assessment'] = "minor"
            report['recommended_actions'] = [
                "Standard designer review and polish",
                "Minor content adjustments needed"
            ]
        
        return report
    
    def should_regenerate(self, assessment_results: Dict, current_regenerations: int) -> bool:
        """
        Determine if content should be regenerated or escalated to human
        
        Args:
            assessment_results: Quality assessment results
            current_regenerations: Current regeneration count
            
        Returns:
            True if should regenerate, False if should escalate to human
        """
        
        if current_regenerations >= self.max_regenerations:
            return False
            
        # Check if issues are fixable via regeneration
        severity_count = {"minor": 0, "moderate": 0, "major": 0}
        
        for assessment in assessment_results.get('content_assessments', {}).values():
            severity = assessment.get('severity', 'moderate')
            severity_count[severity] += 1
        
        # If too many major issues, escalate immediately
        if severity_count['major'] > 2:
            return False
        
        # If mostly minor/moderate issues, try regeneration
        return True

# Quality Control Integration Functions
def assess_campaign_quality(campaign_id: str, content_data: Dict, brand_context: Dict) -> Dict:
    """
    Main function to assess campaign content quality
    
    Args:
        campaign_id: Campaign identifier
        content_data: Generated content to assess
        brand_context: Brand information for context
        
    Returns:
        Quality assessment results
    """
    
    agent = QualityControlAgent()
    return agent.process_campaign_content(campaign_id, content_data, brand_context)

def handle_quality_failure(campaign_id: str, assessment_results: Dict, regeneration_count: int) -> Dict:
    """
    Handle content that fails quality control
    
    Args:
        campaign_id: Campaign identifier
        assessment_results: Quality assessment results
        regeneration_count: Number of regeneration attempts
        
    Returns:
        Next actions to take (regenerate or escalate)
    """
    
    agent = QualityControlAgent()
    
    response = {
        "action": "escalate_to_human",
        "regenerate": False,
        "failure_report": None,
        "user_message": None
    }
    
    if agent.should_regenerate(assessment_results, regeneration_count):
        response["action"] = "regenerate"
        response["regenerate"] = True
        response["regeneration_guidance"] = []
        
        # Provide specific guidance for regeneration
        for failed_item in assessment_results.get('failed_content', []):
            response["regeneration_guidance"].append({
                'content_id': failed_item.get('id'),
                'recommendations': failed_item.get('recommendations', [])
            })
    else:
        # Generate failure report for admin
        failure_report = agent.generate_failure_report(assessment_results, regeneration_count)
        response["failure_report"] = failure_report
        
        # Generate user-friendly message
        response["user_message"] = generate_user_failure_message(assessment_results, regeneration_count)
    
    return response

def generate_user_failure_message(assessment_results: Dict, regeneration_count: int) -> str:
    """
    Generate user-friendly message for quality control failures
    """
    
    quality_summary = assessment_results.get('quality_summary', {})
    failed_pieces = quality_summary.get('failed_pieces', 0)
    
    message = f"""
    We maintain the highest quality standards at Dominate Marketing. 
    
    After {regeneration_count} optimization attempts, {failed_pieces} content pieces 
    require additional refinement to meet our premium quality criteria.
    
    Our live design team has been notified and will personally review and enhance 
    your content to ensure it exceeds expectations. You'll receive the improved 
    content within 24 hours.
    
    We appreciate your patience as we deliver content that truly dominates your market.
    """
    
    return message.strip()