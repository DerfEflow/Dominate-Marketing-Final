"""
Pika Labs Service Integration
Handles image-to-video manipulation and enhancement
"""
import os
import json
import time
import logging
import requests
from typing import Dict, Any, Optional, List
from models import SubscriptionTier
from .ai_models import APIKeyManager

logger = logging.getLogger(__name__)

class PikaLabsService:
    """Pika Labs service for image-to-video manipulation"""
    
    def __init__(self):
        self.api_key = APIKeyManager.get_pika_key()
        self.base_url = "https://api.pikalabs.ai/v1"  # Placeholder URL
        self.model = "pika-1.5"  # Same for all tiers
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def image_to_video(self, 
                      image_url: str,
                      motion_prompt: str,
                      subscription_tier: SubscriptionTier,
                      duration: int = 3,
                      motion_strength: float = 0.8) -> Dict[str, Any]:
        """
        Convert static image to animated video using Pika Labs
        Perfect for bringing marketing images to life
        """
        
        logger.info(f"Converting image to video with Pika Labs for {subscription_tier.value} tier")
        
        try:
            payload = {
                "model": self.model,
                "image_url": image_url,
                "motion_prompt": motion_prompt,
                "duration": duration,
                "motion_strength": motion_strength,
                "resolution": "1024x1024",
                "fps": 24,
                "format": "mp4"
            }
            
            response = requests.post(
                f"{self.base_url}/image-to-video",
                headers=self.headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Process successful response
                video_data = {
                    'success': True,
                    'job_id': result.get('job_id'),
                    'video_url': result.get('video_url'),
                    'preview_url': result.get('preview_url'),
                    'status': result.get('status', 'processing'),
                    'model_used': self.model,
                    'tier': subscription_tier.value,
                    'duration': duration,
                    'motion_strength': motion_strength,
                    'created_at': time.time()
                }
                
                return video_data
            
            else:
                error_msg = f"Pika Labs API error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return {
                    'success': False,
                    'error': error_msg,
                    'video_url': None
                }
        
        except Exception as e:
            logger.error(f"Error with Pika Labs image-to-video: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'video_url': None,
                'model_used': self.model,
                'tier': subscription_tier.value
            }
    
    def enhance_video(self,
                     video_url: str,
                     enhancement_type: str,
                     subscription_tier: SubscriptionTier) -> Dict[str, Any]:
        """
        Enhance existing video with Pika Labs effects
        Types: 'upscale', 'stabilize', 'color_enhance', 'motion_blur'
        """
        
        logger.info(f"Enhancing video with {enhancement_type} for {subscription_tier.value} tier")
        
        try:
            payload = {
                "model": self.model,
                "video_url": video_url,
                "enhancement_type": enhancement_type,
                "quality": "high" if subscription_tier in [SubscriptionTier.PRO, SubscriptionTier.ENTERPRISE] else "standard"
            }
            
            response = requests.post(
                f"{self.base_url}/enhance-video",
                headers=self.headers,
                json=payload,
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                
                return {
                    'success': True,
                    'job_id': result.get('job_id'),
                    'enhanced_video_url': result.get('video_url'),
                    'original_video_url': video_url,
                    'enhancement_type': enhancement_type,
                    'status': result.get('status', 'processing'),
                    'model_used': self.model,
                    'tier': subscription_tier.value
                }
            
            else:
                error_msg = f"Enhancement failed: {response.status_code} - {response.text}"
                return {
                    'success': False,
                    'error': error_msg
                }
        
        except Exception as e:
            logger.error(f"Error enhancing video: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_motion_sequences(self,
                              images: List[str],
                              transition_prompts: List[str],
                              subscription_tier: SubscriptionTier) -> Dict[str, Any]:
        """
        Create smooth motion sequences between multiple images
        Perfect for creating dynamic product showcases
        """
        
        if len(images) != len(transition_prompts):
            return {
                'success': False,
                'error': 'Number of images must match number of transition prompts'
            }
        
        logger.info(f"Creating motion sequence with {len(images)} images for {subscription_tier.value} tier")
        
        try:
            payload = {
                "model": self.model,
                "images": images,
                "transition_prompts": transition_prompts,
                "sequence_duration": 6,  # 2 seconds per image
                "transition_duration": 1,
                "loop": True,
                "quality": "high" if subscription_tier in [SubscriptionTier.PRO, SubscriptionTier.ENTERPRISE] else "standard"
            }
            
            response = requests.post(
                f"{self.base_url}/motion-sequence",
                headers=self.headers,
                json=payload,
                timeout=180
            )
            
            if response.status_code == 200:
                result = response.json()
                
                return {
                    'success': True,
                    'job_id': result.get('job_id'),
                    'sequence_video_url': result.get('video_url'),
                    'preview_url': result.get('preview_url'),
                    'status': result.get('status', 'processing'),
                    'images_count': len(images),
                    'model_used': self.model,
                    'tier': subscription_tier.value
                }
            
            else:
                error_msg = f"Motion sequence failed: {response.status_code} - {response.text}"
                return {
                    'success': False,
                    'error': error_msg
                }
        
        except Exception as e:
            logger.error(f"Error creating motion sequence: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def generate_motion_prompts(self,
                              campaign_data: Dict[str, Any],
                              image_descriptions: List[str]) -> List[str]:
        """
        Generate motion prompts for image-to-video conversion
        Based on campaign goals and image content
        """
        
        motion_prompts = []
        campaign_goal = campaign_data.get('campaign_goal', 'engagement')
        
        for i, description in enumerate(image_descriptions):
            if campaign_goal == 'sales':
                prompts = [
                    "gentle zoom in with elegant glow effect",
                    "smooth pan right with product highlight",
                    "subtle rotation with sparkle particles",
                    "zoom out reveal with confident energy"
                ]
            elif campaign_goal == 'awareness':
                prompts = [
                    "dynamic zoom with brand colors flowing",
                    "smooth parallax movement with floating elements",
                    "gentle wave motion with light rays",
                    "spiral zoom with energy burst"
                ]
            elif campaign_goal == 'engagement':
                prompts = [
                    "playful bounce with colorful particles",
                    "rhythmic pulse with social media icons",
                    "smooth drift with interactive elements",
                    "gentle shake with attention-grabbing effects"
                ]
            else:
                prompts = [
                    "smooth zoom in with professional lighting",
                    "elegant pan movement with subtle effects",
                    "gentle rotation with premium feel",
                    "confident zoom out with brand energy"
                ]
            
            # Select prompt based on image index
            motion_prompts.append(prompts[i % len(prompts)])
        
        return motion_prompts
    
    def check_job_status(self, job_id: str) -> Dict[str, Any]:
        """Check the status of a Pika Labs job"""
        
        try:
            response = requests.get(
                f"{self.base_url}/jobs/{job_id}",
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    'job_id': job_id,
                    'status': 'error',
                    'error': f"API error: {response.status_code}"
                }
        
        except Exception as e:
            logger.error(f"Error checking job status: {str(e)}")
            return {
                'job_id': job_id,
                'status': 'error',
                'error': str(e)
            }
    
    def get_available_effects(self) -> List[Dict[str, Any]]:
        """Get list of available motion effects"""
        
        return [
            {
                'name': 'zoom_in',
                'description': 'Smooth zoom into the subject',
                'best_for': ['product_focus', 'call_to_action']
            },
            {
                'name': 'pan_right',
                'description': 'Horizontal pan movement',
                'best_for': ['landscape', 'product_showcase']
            },
            {
                'name': 'rotate_360',
                'description': 'Full rotation around center',
                'best_for': ['product_demo', 'logo_reveal']
            },
            {
                'name': 'parallax',
                'description': 'Depth-based movement',
                'best_for': ['hero_sections', 'backgrounds']
            },
            {
                'name': 'pulse',
                'description': 'Rhythmic scaling effect',
                'best_for': ['attention_grabbing', 'music_sync']
            },
            {
                'name': 'float',
                'description': 'Gentle floating motion',
                'best_for': ['elegant_brands', 'luxury_products']
            }
        ]