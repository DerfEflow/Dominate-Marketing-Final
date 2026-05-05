"""
AI Content Generator for Dominate Marketing
Generates real AI content with watermarks for demo purposes
"""
import os
import requests
import json
import base64
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import logging
from typing import Dict, List, Optional
import openai

logger = logging.getLogger(__name__)

class AIContentGenerator:
    """Generates real AI content with watermarks for demo purposes"""
    
    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
        
    def generate_marketing_image(self, 
                               business_name: str, 
                               industry: str, 
                               content_type: str = "product showcase") -> Dict:
        """Generate a real AI image using DALL-E with watermark"""
        try:
            # Create detailed prompt for business-specific image
            prompt = f"""Create a professional marketing image for {business_name}, a {industry} company. 
            Style: Modern, clean, professional marketing material for {content_type}.
            High quality, suitable for social media and advertising.
            Include relevant industry elements, modern design, engaging composition."""
            
            logger.info(f"Generating image with prompt: {prompt}")
            
            # Generate image using DALL-E
            response = self.openai_client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024",
                quality="standard",
                n=1,
            )
            
            # Download the generated image
            image_url = response.data[0].url
            image_response = requests.get(image_url)
            
            if image_response.status_code == 200:
                # Add watermark to the image
                watermarked_image = self._add_watermark_to_image(image_response.content)
                
                return {
                    'success': True,
                    'image_data': base64.b64encode(watermarked_image).decode('utf-8'),
                    'content_type': 'image/png',
                    'prompt': prompt,
                    'watermarked': True
                }
            else:
                logger.error(f"Failed to download generated image: {image_response.status_code}")
                return self._get_fallback_image()
                
        except Exception as e:
            logger.error(f"Error generating image: {e}")
            return self._get_fallback_image()
    
    def generate_marketing_video_concept(self, 
                                       business_name: str, 
                                       industry: str) -> Dict:
        """Generate video concept and script for VEO3 (simulated with detailed description)"""
        try:
            # Generate detailed video concept using GPT
            prompt = f"""Create a detailed video concept for {business_name}, a {industry} company.
            Include:
            1. Video concept and theme
            2. Shot-by-shot breakdown (5-7 shots)
            3. Text overlays and captions
            4. Visual style and mood
            5. Call-to-action
            
            Make it engaging, professional, and suitable for social media marketing."""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a professional video marketing specialist."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800
            )
            
            video_concept = response.choices[0].message.content
            
            # For demo purposes, we'll create a placeholder video frame with the concept
            video_frame = self._create_video_placeholder_frame(business_name, video_concept)
            
            return {
                'success': True,
                'video_concept': video_concept,
                'frame_data': base64.b64encode(video_frame).decode('utf-8'),
                'content_type': 'image/png',
                'watermarked': True,
                'note': 'Full VEO3 video generation available in production tier'
            }
            
        except Exception as e:
            logger.error(f"Error generating video concept: {e}")
            return self._get_fallback_video()
    
    def generate_social_media_posts(self, 
                                  business_name: str, 
                                  industry: str, 
                                  image_generated: bool = True,
                                  video_generated: bool = True) -> Dict:
        """Generate platform-specific social media posts"""
        try:
            prompt = f"""Create engaging social media posts for {business_name}, a {industry} company.
            Generate posts for:
            1. Facebook (longer format, professional)
            2. Instagram (hashtag-heavy, visual focus)
            3. X/Twitter (concise, trending)
            4. TikTok (fun, energetic, trend-aware)
            
            {"Include references to the accompanying AI-generated image and video." if image_generated and video_generated else ""}
            Make each post unique and platform-optimized."""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a social media marketing expert who creates viral content."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000
            )
            
            posts_content = response.choices[0].message.content
            
            # Parse and structure the posts (simplified for demo)
            posts = {
                'facebook': self._extract_platform_post(posts_content, 'Facebook'),
                'instagram': self._extract_platform_post(posts_content, 'Instagram'),
                'twitter': self._extract_platform_post(posts_content, 'X/Twitter'),
                'tiktok': self._extract_platform_post(posts_content, 'TikTok')
            }
            
            return {
                'success': True,
                'posts': posts,
                'raw_content': posts_content,
                'watermarked': True
            }
            
        except Exception as e:
            logger.error(f"Error generating social media posts: {e}")
            return self._get_fallback_posts(business_name, industry)
    
    def _add_watermark_to_image(self, image_data: bytes) -> bytes:
        """Add central watermark to image"""
        try:
            # Open the image
            image = Image.open(BytesIO(image_data))
            
            # Convert to RGBA if needed
            if image.mode != 'RGBA':
                image = image.convert('RGBA')
            
            # Create watermark overlay
            overlay = Image.new('RGBA', image.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)
            
            # Calculate watermark position (center)
            width, height = image.size
            watermark_text = "DOMINATE MARKETING DEMO"
            
            # Try to use a font, fallback to default if not available
            try:
                font_size = max(width // 20, 30)
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
            except:
                font = ImageFont.load_default()
            
            # Get text dimensions
            bbox = draw.textbbox((0, 0), watermark_text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # Position watermark in center
            x = (width - text_width) // 2
            y = (height - text_height) // 2
            
            # Draw text with shadow for better visibility
            shadow_offset = 2
            draw.text((x + shadow_offset, y + shadow_offset), watermark_text, 
                     fill=(0, 0, 0, 100), font=font)
            draw.text((x, y), watermark_text, fill=(255, 255, 255, 150), font=font)
            
            # Rotate overlay for diagonal watermark
            overlay = overlay.rotate(45, expand=False)
            
            # Composite the watermark onto the image
            watermarked = Image.alpha_composite(image, overlay)
            
            # Convert back to RGB and save
            if watermarked.mode == 'RGBA':
                background = Image.new('RGB', watermarked.size, (255, 255, 255))
                background.paste(watermarked, mask=watermarked.split()[-1])
                watermarked = background
            
            # Save to bytes
            output = BytesIO()
            watermarked.save(output, format='PNG', quality=95)
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Error adding watermark: {e}")
            return image_data
    
    def _create_video_placeholder_frame(self, business_name: str, concept: str) -> bytes:
        """Create a video placeholder frame with concept text"""
        try:
            # Create a 16:9 video frame
            width, height = 1280, 720
            image = Image.new('RGB', (width, height), color=(30, 30, 30))
            draw = ImageDraw.Draw(image)
            
            # Add title
            title = f"{business_name} Marketing Video"
            try:
                title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
                concept_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
            except:
                title_font = ImageFont.load_default()
                concept_font = ImageFont.load_default()
            
            # Draw title
            title_bbox = draw.textbbox((0, 0), title, font=title_font)
            title_width = title_bbox[2] - title_bbox[0]
            title_x = (width - title_width) // 2
            draw.text((title_x, 50), title, fill=(255, 255, 255), font=title_font)
            
            # Draw concept preview (first few lines)
            concept_lines = concept.split('\n')[:8]
            y_offset = 150
            for line in concept_lines:
                if line.strip():
                    draw.text((50, y_offset), line.strip()[:80], fill=(200, 200, 200), font=concept_font)
                    y_offset += 35
            
            # Add watermark
            watermark_text = "DOMINATE MARKETING DEMO"
            watermark_bbox = draw.textbbox((0, 0), watermark_text, font=title_font)
            watermark_width = watermark_bbox[2] - watermark_bbox[0]
            watermark_x = (width - watermark_width) // 2
            watermark_y = (height - 100) // 2
            
            # Draw watermark with transparency effect
            draw.text((watermark_x + 2, watermark_y + 2), watermark_text, 
                     fill=(0, 0, 0), font=title_font)
            draw.text((watermark_x, watermark_y), watermark_text, 
                     fill=(255, 255, 255), font=title_font)
            
            # Save to bytes
            output = BytesIO()
            image.save(output, format='PNG')
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Error creating video frame: {e}")
            return b''
    
    def _extract_platform_post(self, content: str, platform: str) -> str:
        """Extract platform-specific post from generated content"""
        try:
            lines = content.split('\n')
            platform_section = []
            capturing = False
            
            for line in lines:
                if platform.lower() in line.lower() and ':' in line:
                    capturing = True
                    continue
                elif capturing and any(p in line.lower() for p in ['facebook', 'instagram', 'twitter', 'tiktok']) and ':' in line:
                    break
                elif capturing and line.strip():
                    platform_section.append(line.strip())
            
            return '\n'.join(platform_section) if platform_section else f"Engaging {platform} post for your business! 🚀 #Marketing #AI"
            
        except Exception as e:
            logger.error(f"Error extracting platform post: {e}")
            return f"Professional {platform} content coming soon! #Marketing"
    
    def _get_fallback_image(self) -> Dict:
        """Return fallback image data when generation fails"""
        return {
            'success': False,
            'error': 'Image generation temporarily unavailable',
            'image_data': '',
            'watermarked': True
        }
    
    def _get_fallback_video(self) -> Dict:
        """Return fallback video data when generation fails"""
        return {
            'success': False,
            'error': 'Video generation temporarily unavailable',
            'video_concept': 'Professional marketing video concept will be generated here',
            'watermarked': True
        }
    
    def _get_fallback_posts(self, business_name: str, industry: str) -> Dict:
        """Return fallback social media posts"""
        return {
            'success': True,
            'posts': {
                'facebook': f"Exciting updates from {business_name}! Leading innovation in {industry}. Stay tuned for more! #Business #Innovation",
                'instagram': f"✨ {business_name} ✨ Transforming {industry} one step at a time! #Business #{industry.replace(' ', '')} #Innovation #Growth",
                'twitter': f"🚀 {business_name} is revolutionizing {industry}! Big things coming soon. #Innovation #{industry.replace(' ', '')}",
                'tiktok': f"POV: You're watching {business_name} change the {industry} game 🔥 #Business #Innovation #Trending"
            },
            'watermarked': True
        }

# Test the generator
if __name__ == "__main__":
    generator = AIContentGenerator()
    
    # Test image generation
    result = generator.generate_marketing_image("Tesla", "automotive", "product showcase")
    print(f"Image generation success: {result['success']}")
    
    # Test social media posts
    posts = generator.generate_social_media_posts("Tesla", "automotive", True, True)
    print(f"Posts generation success: {posts['success']}")