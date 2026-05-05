"""
Google VEO 3 Service Integration
Handles video generation using Google's VEO 3 model
"""
import os
import json
import time
import logging
from typing import Dict, Any, Optional, List
from google import genai
from google.genai import types
from models import SubscriptionTier
from .ai_models import APIKeyManager

logger = logging.getLogger(__name__)

class GoogleVEOService:
    """Google VEO 3 service for video generation"""
    
    def __init__(self):
        self.client = genai.Client(api_key=APIKeyManager.get_google_key())
        self.model = "veo-3"  # Same for all tiers as specified
    
    def generate_video(self, 
                      video_script: Dict[str, Any],
                      image_prompts: List[Dict[str, Any]],
                      subscription_tier: SubscriptionTier,
                      duration: int = 30,
                      resolution: str = "1080p") -> Dict[str, Any]:
        """
        Generate video using Google VEO 3
        Creates professional video content from script and visual prompts
        """
        
        logger.info(f"Generating video with VEO 3 for {subscription_tier.value} tier")
        
        try:
            # Build comprehensive video prompt
            video_prompt = self._build_video_generation_prompt(
                video_script, image_prompts, duration, resolution
            )
            
            # Generate video with VEO 3
            response = self.client.models.generate_content(
                model=self.model,
                contents=[
                    types.Content(
                        role="user", 
                        parts=[types.Part(text=video_prompt)]
                    )
                ],
                config=types.GenerateContentConfig(
                    response_modalities=['VIDEO'],
                    video_config={
                        'duration_seconds': duration,
                        'resolution': resolution,
                        'frame_rate': 30,
                        'format': 'mp4'
                    }
                )
            )
            
            # Process response
            if response.candidates and response.candidates[0].content:
                video_data = self._process_video_response(response, video_script)
                
                # Add metadata
                video_data.update({
                    'model_used': self.model,
                    'tier': subscription_tier.value,
                    'duration': duration,
                    'resolution': resolution,
                    'generated_at': time.time()
                })
                
                return video_data
            
            else:
                raise Exception("No video content generated")
        
        except Exception as e:
            logger.error(f"Error generating video with VEO 3: {str(e)}")
            # Return structured error response
            return {
                'success': False,
                'error': str(e),
                'video_url': None,
                'preview_url': None,
                'model_used': self.model,
                'tier': subscription_tier.value
            }
    
    def generate_video_variations(self,
                                base_script: Dict[str, Any],
                                subscription_tier: SubscriptionTier,
                                variation_count: int = 3) -> List[Dict[str, Any]]:
        """Generate multiple video variations for A/B testing"""
        
        variations = []
        
        for i in range(variation_count):
            try:
                # Modify script for variation
                varied_script = self._create_script_variation(base_script, i)
                
                # Generate video variation
                video_result = self.generate_video(
                    varied_script, 
                    [],  # Empty image prompts for variations
                    subscription_tier,
                    duration=30
                )
                
                video_result['variation_id'] = i + 1
                variations.append(video_result)
                
            except Exception as e:
                logger.error(f"Error generating video variation {i+1}: {str(e)}")
                variations.append({
                    'variation_id': i + 1,
                    'success': False,
                    'error': str(e)
                })
        
        return variations
    
    def _build_video_generation_prompt(self,
                                     video_script: Dict[str, Any],
                                     image_prompts: List[Dict[str, Any]],
                                     duration: int,
                                     resolution: str) -> str:
        """Build comprehensive prompt for video generation"""
        
        scenes = video_script.get('scenes', [])
        title = video_script.get('title', 'Marketing Video')
        
        prompt = f"""
        Create a {duration}-second professional marketing video: "{title}"
        
        TECHNICAL SPECIFICATIONS:
        - Duration: {duration} seconds
        - Resolution: {resolution}
        - Format: MP4, optimized for social media
        - Aspect Ratio: 9:16 (vertical for mobile)
        - Frame Rate: 30fps
        
        VIDEO SCENES:
        """
        
        for i, scene in enumerate(scenes):
            prompt += f"""
        Scene {i+1} ({scene.get('timing', 'Unknown')}):
        - Visuals: {scene.get('visual_description', '')}
        - Text Overlay: {scene.get('text_overlay', '')}
        - Voiceover: {scene.get('voiceover', '')}
        - Transition: {scene.get('transition', 'smooth')}
        """
        
        # Add image prompt context
        if image_prompts:
            prompt += "\nVISUAL STYLE REFERENCES:\n"
            for i, img_prompt in enumerate(image_prompts[:3]):  # Limit to 3
                prompt += f"- Style {i+1}: {img_prompt.get('style', '')}\n"
        
        prompt += """
        
        PRODUCTION REQUIREMENTS:
        - High-quality, broadcast-ready output
        - Smooth transitions between scenes
        - Professional color grading
        - Clear, readable text overlays
        - Engaging visual effects
        - Mobile-optimized composition
        - Viral content structure (hook, problem, solution, CTA)
        
        Generate a video that stops scrolling and drives immediate action.
        """
        
        return prompt
    
    def _process_video_response(self, 
                              response: Any, 
                              video_script: Dict[str, Any]) -> Dict[str, Any]:
        """Process VEO 3 response and extract video data"""
        
        try:
            content = response.candidates[0].content
            
            # Extract video data from response
            video_data = {
                'success': True,
                'video_url': None,  # Will be populated by VEO response
                'preview_url': None,  # Thumbnail/preview
                'title': video_script.get('title', 'Generated Video'),
                'duration': video_script.get('duration', 30),
                'scenes_count': len(video_script.get('scenes', [])),
                'description': video_script.get('description', ''),
                'file_size': None,  # Will be populated by actual response
                'processing_status': 'completed'
            }
            
            # Process actual video content from VEO response
            if content.parts:
                for part in content.parts:
                    if hasattr(part, 'video_data'):
                        # Extract video URL and metadata
                        video_data['video_url'] = getattr(part.video_data, 'url', None)
                        video_data['file_size'] = getattr(part.video_data, 'size', None)
                    elif hasattr(part, 'text'):
                        # Extract additional metadata from text response
                        try:
                            metadata = json.loads(part.text)
                            video_data.update(metadata)
                        except:
                            pass
            
            return video_data
            
        except Exception as e:
            logger.error(f"Error processing VEO response: {str(e)}")
            return {
                'success': False,
                'error': f"Failed to process video response: {str(e)}",
                'video_url': None
            }
    
    def _create_script_variation(self, 
                               base_script: Dict[str, Any], 
                               variation_index: int) -> Dict[str, Any]:
        """Create script variation for A/B testing"""
        
        variation = base_script.copy()
        
        # Modify based on variation type
        if variation_index == 0:
            # Variation 1: More aggressive hook
            variation['title'] = f"[URGENT] {variation.get('title', '')}"
        elif variation_index == 1:
            # Variation 2: Social proof focus
            variation['title'] = f"Why 10,000+ Customers Choose {variation.get('title', '')}"
        elif variation_index == 2:
            # Variation 3: Problem-focused
            variation['title'] = f"Stop Wasting Money - {variation.get('title', '')}"
        
        variation['variation_type'] = f"variation_{variation_index + 1}"
        
        return variation
    
    def check_video_status(self, video_id: str) -> Dict[str, Any]:
        """Check the processing status of a video"""
        
        try:
            # Implementation depends on VEO API structure
            # This is a placeholder for status checking
            return {
                'video_id': video_id,
                'status': 'completed',  # or 'processing', 'failed'
                'progress': 100,
                'estimated_completion': None
            }
            
        except Exception as e:
            logger.error(f"Error checking video status: {str(e)}")
            return {
                'video_id': video_id,
                'status': 'error',
                'error': str(e)
            }