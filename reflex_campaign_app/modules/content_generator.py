"""
Content Generator using latest AI models
Generates images, videos (VEO 3), and text content based on authentic data
"""

import logging
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from openai import OpenAI
from google import genai

logger = logging.getLogger(__name__)

class ContentGenerator:
    """
    Generates multi-modal content using latest AI models
    - Images: DALL-E 3 via OpenAI
    - Videos: VEO 3 via Google (when available)
    - Text: Latest GPT models via OpenAI
    """
    
    def __init__(self):
        # OpenAI setup
        self.openai_key = os.environ.get('OPENAI_API_KEY')
        if not self.openai_key:
            raise Exception("OpenAI API key not configured")
        self.openai_client = OpenAI(api_key=self.openai_key)
        
        # Google setup for VEO 3
        self.google_key = os.environ.get('GOOGLE_API_KEY') 
        self.google_client = genai.Client(api_key=self.google_key) if self.google_key else None
        
        # Latest models
        self.text_model = "gpt-4o"  # Latest text generation
        self.image_model = "dall-e-3"  # Latest image generation
        self.video_model = "veo-3"  # VEO 3 when available
    
    def generate_all_content(self, content_prompts: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate all content types from prompts
        """
        logger.info("Starting comprehensive content generation")
        
        generated_content = {
            'images': [],
            'videos': [],
            'texts': [],
            'generation_summary': {
                'started_at': datetime.now().isoformat(),
                'models_used': {
                    'text': self.text_model,
                    'image': self.image_model, 
                    'video': self.video_model
                }
            }
        }
        
        # Generate images
        if 'image_prompts' in content_prompts:
            generated_content['images'] = self._generate_images(content_prompts['image_prompts'])
        
        # Generate videos
        if 'video_prompts' in content_prompts:
            generated_content['videos'] = self._generate_videos(content_prompts['video_prompts'])
        
        # Generate text content
        if 'text_prompts' in content_prompts:
            generated_content['texts'] = self._generate_texts(content_prompts['text_prompts'])
        
        # Update summary
        generated_content['generation_summary'].update({
            'completed_at': datetime.now().isoformat(),
            'total_images': len(generated_content['images']),
            'total_videos': len(generated_content['videos']),
            'total_texts': len(generated_content['texts'])
        })
        
        logger.info(f"Content generation completed: {len(generated_content['images'])} images, {len(generated_content['videos'])} videos, {len(generated_content['texts'])} texts")
        return generated_content
    
    def _generate_images(self, image_prompts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate images using DALL-E 3"""
        logger.info(f"Generating {len(image_prompts)} images with DALL-E 3")
        images = []
        
        for prompt_data in image_prompts:
            try:
                response = self.openai_client.images.generate(
                    model=self.image_model,
                    prompt=prompt_data['prompt'],
                    size="1024x1024",
                    quality="hd",  # High quality for professional use
                    style="vivid",  # Enhanced style for marketing content
                    n=1
                )
                
                image_result = {
                    'id': prompt_data['id'],
                    'title': prompt_data['title'],
                    'url': response.data[0].url,
                    'prompt_used': prompt_data['prompt'],
                    'style': prompt_data.get('style', 'professional'),
                    'target_platform': prompt_data.get('target_platform', 'general'),
                    'model_used': self.image_model,
                    'quality': 'hd',
                    'generated_at': datetime.now().isoformat(),
                    'status': 'success'
                }
                images.append(image_result)
                
                logger.info(f"Generated image: {prompt_data['title']}")
                
            except Exception as e:
                logger.error(f"Image generation failed for {prompt_data['id']}: {e}")
                images.append({
                    'id': prompt_data['id'],
                    'title': prompt_data['title'],
                    'error': str(e),
                    'status': 'failed',
                    'generated_at': datetime.now().isoformat()
                })
        
        return images
    
    def _generate_videos(self, video_prompts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate videos using VEO 3"""
        logger.info(f"Generating {len(video_prompts)} videos with VEO 3")
        videos = []
        
        if not self.google_client:
            logger.warning("Google API not configured - cannot generate videos")
            for prompt_data in video_prompts:
                videos.append({
                    'id': prompt_data['id'],
                    'title': prompt_data['title'],
                    'error': 'Google API key not configured',
                    'status': 'failed',
                    'generated_at': datetime.now().isoformat()
                })
            return videos
        
        for prompt_data in video_prompts:
            try:
                # VEO 3 video generation
                # Note: This is prepared for VEO 3 - will need to be updated when API is available
                video_prompt = prompt_data['prompt']
                duration = prompt_data.get('duration', '30s')
                
                # For now, create detailed video concepts that will be ready for VEO 3
                video_concept = self._create_video_concept(video_prompt, duration)
                
                video_result = {
                    'id': prompt_data['id'],
                    'title': prompt_data['title'],
                    'concept': video_concept,
                    'prompt_used': video_prompt,
                    'duration': duration,
                    'style': prompt_data.get('style', 'professional'),
                    'model_target': self.video_model,
                    'status': 'concept_ready',  # Ready for VEO 3 when available
                    'note': 'Video concept prepared for VEO 3 generation',
                    'generated_at': datetime.now().isoformat()
                }
                videos.append(video_result)
                
                logger.info(f"Video concept created: {prompt_data['title']}")
                
            except Exception as e:
                logger.error(f"Video concept creation failed for {prompt_data['id']}: {e}")
                videos.append({
                    'id': prompt_data['id'],
                    'title': prompt_data['title'],
                    'error': str(e),
                    'status': 'failed',
                    'generated_at': datetime.now().isoformat()
                })
        
        return videos
    
    def _generate_texts(self, text_prompts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate text content using latest GPT model"""
        logger.info(f"Generating {len(text_prompts)} text pieces with {self.text_model}")
        texts = []
        
        for prompt_data in text_prompts:
            try:
                platform = prompt_data.get('platform', 'general')
                tone = prompt_data.get('tone', 'professional')
                
                system_message = self._create_text_system_message(platform, tone)
                
                response = self.openai_client.chat.completions.create(
                    model=self.text_model,
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": prompt_data['prompt']}
                    ],
                    max_tokens=500,
                    temperature=0.8
                )
                
                text_result = {
                    'id': prompt_data['id'],
                    'title': prompt_data['title'],
                    'content': response.choices[0].message.content.strip(),
                    'platform': platform,
                    'tone': tone,
                    'prompt_used': prompt_data['prompt'],
                    'model_used': self.text_model,
                    'word_count': len(response.choices[0].message.content.strip().split()),
                    'generated_at': datetime.now().isoformat(),
                    'status': 'success'
                }
                texts.append(text_result)
                
                logger.info(f"Generated text: {prompt_data['title']} ({text_result['word_count']} words)")
                
            except Exception as e:
                logger.error(f"Text generation failed for {prompt_data['id']}: {e}")
                texts.append({
                    'id': prompt_data['id'],
                    'title': prompt_data['title'],
                    'error': str(e),
                    'status': 'failed',
                    'generated_at': datetime.now().isoformat()
                })
        
        return texts
    
    def _create_video_concept(self, prompt: str, duration: str) -> str:
        """Create detailed video concept for VEO 3 generation"""
        concept_prompt = f"""
        Create a detailed video concept for VEO 3 generation based on this prompt:
        {prompt}
        Duration: {duration}
        
        Provide a shot-by-shot breakdown that VEO 3 can execute.
        """
        
        try:
            response = self.openai_client.chat.completions.create(
                model=self.text_model,
                messages=[
                    {"role": "system", "content": "You are a video production expert. Create detailed video concepts with specific visual descriptions for AI video generation."},
                    {"role": "user", "content": concept_prompt}
                ],
                max_tokens=300,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Video concept creation failed: {e}")
            return f"Video concept for: {prompt} (Duration: {duration})"
    
    def _create_text_system_message(self, platform: str, tone: str) -> str:
        """Create platform-specific system messages for text generation"""
        platform_guidelines = {
            'instagram': "Create engaging Instagram content with emojis, hashtags, and visual storytelling focus.",
            'facebook': "Write Facebook content that encourages engagement, sharing, and community interaction.",
            'twitter': "Generate concise Twitter content under 280 characters with trending hashtag awareness.",
            'linkedin': "Create professional LinkedIn content that demonstrates expertise and industry insights.",
            'email': "Write compelling email content with clear subject lines and strong call-to-action.",
            'website': "Generate website copy that is SEO-friendly, conversion-focused, and user-centric.",
            'general': "Create high-quality marketing content appropriate for multiple channels."
        }
        
        tone_guidelines = {
            'professional': "Use a professional, authoritative tone that builds trust and credibility.",
            'engaging': "Write in an engaging, conversational tone that captures attention and encourages interaction.",
            'persuasive': "Use persuasive language that motivates action and drives conversions.",
            'informative': "Present information clearly and comprehensively while maintaining reader interest.",
            'intriguing': "Create curiosity and intrigue that compels readers to learn more."
        }
        
        platform_guide = platform_guidelines.get(platform, platform_guidelines['general'])
        tone_guide = tone_guidelines.get(tone, tone_guidelines['professional'])
        
        return f"You are an expert marketing copywriter. {platform_guide} {tone_guide} Ensure all content is authentic, valuable, and aligns with the brand voice."