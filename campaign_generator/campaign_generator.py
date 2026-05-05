"""
Campaign Generator Module - Reflex Implementation
Comprehensive AI-powered marketing campaign generation from a single URL input
"""

import os
import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from urllib.parse import urlparse
import uuid

import reflex as rx
import requests
from openai import OpenAI
from google import genai
import trafilatura
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CampaignState(rx.State):
    """Reflex state management for campaign generation"""
    
    # User inputs
    url_input: str = ""
    
    # Process status
    is_processing: bool = False
    current_step: str = ""
    progress_percentage: int = 0
    
    # Campaign data
    campaign_id: str = ""
    website_data: Dict[str, Any] = {}
    competitors: List[Dict[str, Any]] = []
    marketing_strategy: Dict[str, Any] = {}
    content_prompts: Dict[str, Any] = {}
    generated_content: Dict[str, Any] = {}
    
    # Status messages
    status_messages: List[str] = []
    error_message: str = ""

class CampaignGenerator:
    """
    Comprehensive AI-powered campaign generator
    Handles entire workflow from URL input to final content generation
    """
    
    def __init__(self):
        """Initialize the campaign generator with API clients"""
        # Initialize OpenAI client
        self.openai_api_key = os.environ.get('OPENAI_API_KEY')
        self.openai_client = OpenAI(api_key=self.openai_api_key) if self.openai_api_key else None
        
        # Initialize Google client
        self.google_api_key = os.environ.get('GOOGLE_API_KEY')
        self.google_client = genai.Client(api_key=self.google_api_key) if self.google_api_key else None
        
        # Initialize Google Search API
        self.google_search_api_key = os.environ.get('GOOGLE_SEARCH_API_KEY')
        self.google_search_engine_id = os.environ.get('GOOGLE_SEARCH_ENGINE_ID')
        
        # Campaign storage directory
        self.storage_dir = "campaign_storage"
        os.makedirs(self.storage_dir, exist_ok=True)
        
    async def generate_campaign(self, url: str, state: CampaignState) -> Dict[str, Any]:
        """
        Main orchestrator function - handles entire campaign generation workflow
        """
        try:
            # Initialize campaign
            campaign_id = str(uuid.uuid4())
            state.campaign_id = campaign_id
            state.is_processing = True
            state.error_message = ""
            state.status_messages = []
            
            logger.info(f"Starting campaign generation for URL: {url}")
            
            # Step 1: Website Data Scraping
            state.current_step = "Scraping website data"
            state.progress_percentage = 10
            yield
            
            website_data = await self._scrape_website_data(url, state)
            state.website_data = website_data
            
            # Step 2: Competitive Analysis
            state.current_step = "Analyzing competitors"
            state.progress_percentage = 30
            yield
            
            competitors = await self._analyze_competitors(website_data, state)
            state.competitors = competitors
            
            # Step 3: Marketing Strategy Generation
            state.current_step = "Creating marketing strategy"
            state.progress_percentage = 50
            yield
            
            marketing_strategy = await self._generate_marketing_strategy(website_data, competitors, state)
            state.marketing_strategy = marketing_strategy
            
            # Step 4: Content Prompt Generation
            state.current_step = "Generating content prompts"
            state.progress_percentage = 70
            yield
            
            content_prompts = await self._generate_content_prompts(marketing_strategy, state)
            state.content_prompts = content_prompts
            
            # Step 5: AI Content Generation
            state.current_step = "Generating final content"
            state.progress_percentage = 90
            yield
            
            generated_content = await self._generate_ai_content(content_prompts, state)
            state.generated_content = generated_content
            
            # Step 6: Save campaign
            await self._save_campaign_data(campaign_id, {
                'url': url,
                'website_data': website_data,
                'competitors': competitors,
                'marketing_strategy': marketing_strategy,
                'content_prompts': content_prompts,
                'generated_content': generated_content,
                'created_at': datetime.now().isoformat()
            })
            
            state.current_step = "Campaign generation complete"
            state.progress_percentage = 100
            state.is_processing = False
            
            logger.info(f"Campaign generation completed for ID: {campaign_id}")
            yield  # Final yield for async generator
            
        except Exception as e:
            logger.error(f"Campaign generation failed: {str(e)}")
            state.error_message = f"Campaign generation failed: {str(e)}"
            state.is_processing = False
            raise
    
    async def _scrape_website_data(self, url: str, state: CampaignState) -> Dict[str, Any]:
        """
        Scrape website data to understand the product/service
        """
        logger.info(f"Scraping website data from: {url}")
        state.status_messages.append(f"Extracting content from {url}")
        
        try:
            # Download the webpage
            downloaded = trafilatura.fetch_url(url)
            if not downloaded:
                raise Exception("Failed to download webpage content")
            
            # Extract main content in reading mode
            main_content = trafilatura.extract(downloaded, 
                                              include_comments=False,
                                              include_tables=True,
                                              include_images=False)
            
            # Parse HTML for metadata
            soup = BeautifulSoup(downloaded, 'html.parser')
            
            # Extract metadata
            metadata = {
                'title': soup.find('title').text if soup.find('title') else '',
                'description': '',
                'keywords': '',
                'og_title': '',
                'og_description': '',
                'og_image': ''
            }
            
            # Meta description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc:
                metadata['description'] = meta_desc.get('content', '')
            
            # Meta keywords
            meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
            if meta_keywords:
                metadata['keywords'] = meta_keywords.get('content', '')
            
            # Open Graph data
            og_title = soup.find('meta', attrs={'property': 'og:title'})
            if og_title:
                metadata['og_title'] = og_title.get('content', '')
                
            og_desc = soup.find('meta', attrs={'property': 'og:description'})
            if og_desc:
                metadata['og_description'] = og_desc.get('content', '')
                
            og_image = soup.find('meta', attrs={'property': 'og:image'})
            if og_image:
                metadata['og_image'] = og_image.get('content', '')
            
            # Extract business information
            parsed_url = urlparse(url)
            business_name = parsed_url.netloc.replace('www.', '').split('.')[0].title()
            
            website_data = {
                'url': url,
                'business_name': business_name,
                'domain': parsed_url.netloc,
                'main_content': main_content,
                'metadata': metadata,
                'content_length': len(main_content) if main_content else 0,
                'scraped_at': datetime.now().isoformat()
            }
            
            state.status_messages.append(f"Successfully extracted {len(main_content)} characters of content")
            logger.info(f"Website data extracted: {business_name}, {len(main_content)} chars")
            
            return website_data
            
        except Exception as e:
            logger.error(f"Website scraping failed: {str(e)}")
            raise Exception(f"Failed to scrape website: {str(e)}")
    
    async def _analyze_competitors(self, website_data: Dict[str, Any], state: CampaignState) -> List[Dict[str, Any]]:
        """
        Find and analyze top 5 competitors using Google Search API
        """
        logger.info("Analyzing competitors")
        state.status_messages.append("Searching for competitors")
        
        if not self.google_search_api_key or not self.google_search_engine_id:
            logger.warning("Google Search API not configured, using fallback analysis")
            return self._get_fallback_competitors(website_data)
        
        try:
            # Formulate search query based on business information
            business_name = website_data['business_name']
            main_content = website_data['main_content'][:500]  # First 500 chars
            
            # Extract key terms for competitor search
            search_query = f"competitors to {business_name} alternatives"
            
            # Use Google Custom Search API
            search_url = "https://www.googleapis.com/customsearch/v1"
            params = {
                'key': self.google_search_api_key,
                'cx': self.google_search_engine_id,
                'q': search_query,
                'num': 5
            }
            
            response = requests.get(search_url, params=params)
            response.raise_for_status()
            search_results = response.json()
            
            competitors = []
            if 'items' in search_results:
                for item in search_results['items'][:5]:
                    competitor = {
                        'name': item.get('title', ''),
                        'url': item.get('link', ''),
                        'description': item.get('snippet', ''),
                        'found_via': 'google_search'
                    }
                    competitors.append(competitor)
            
            state.status_messages.append(f"Found {len(competitors)} competitors")
            logger.info(f"Found {len(competitors)} competitors via Google Search")
            
            return competitors
            
        except Exception as e:
            logger.error(f"Competitor analysis failed: {str(e)}")
            return self._get_fallback_competitors(website_data)
    
    def _get_fallback_competitors(self, website_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fallback competitor analysis when Google Search API is not available"""
        business_name = website_data['business_name']
        
        # Generic competitor structure for demonstration
        fallback_competitors = [
            {
                'name': f"Alternative to {business_name}",
                'url': "https://example-competitor.com",
                'description': f"A leading competitor in the same industry as {business_name}",
                'found_via': 'fallback_analysis'
            },
            {
                'name': f"{business_name} Alternative",
                'url': "https://competitor-alternative.com", 
                'description': f"Popular alternative service similar to {business_name}",
                'found_via': 'fallback_analysis'
            }
        ]
        
        return fallback_competitors
    
    async def _generate_marketing_strategy(self, website_data: Dict[str, Any], 
                                         competitors: List[Dict[str, Any]], 
                                         state: CampaignState) -> Dict[str, Any]:
        """
        Generate comprehensive marketing strategy using AI
        """
        logger.info("Generating marketing strategy")
        state.status_messages.append("Creating comprehensive marketing strategy")
        
        if not self.openai_client:
            raise Exception("OpenAI API key not configured")
        
        try:
            # Prepare context for strategy generation
            business_context = {
                'business_name': website_data['business_name'],
                'content': website_data['main_content'][:1000],
                'metadata': website_data['metadata'],
                'competitors': [comp['name'] for comp in competitors[:3]]
            }
            
            strategy_prompt = f"""
            Create a comprehensive marketing strategy for the following business:
            
            Business: {business_context['business_name']}
            Description: {business_context['content']}
            Main Competitors: {', '.join(business_context['competitors'])}
            
            Generate a detailed marketing strategy that includes:
            1. Target audience analysis
            2. Unique value proposition 
            3. Content marketing approach for:
               - Image content strategy
               - Video content strategy  
               - Text-based content strategy
            4. Competitive positioning
            5. Key messaging themes
            6. Campaign objectives
            
            Format the response as structured JSON with clear sections for each strategy component.
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",  # Using correct model name
                messages=[
                    {"role": "system", "content": "You are an expert marketing strategist. Create comprehensive, actionable marketing strategies in JSON format."},
                    {"role": "user", "content": strategy_prompt}
                ],
                max_tokens=2000,
                temperature=0.7
            )
            
            strategy_text = response.choices[0].message.content
            
            # Parse JSON response or create structured data
            try:
                marketing_strategy = json.loads(strategy_text)
            except json.JSONDecodeError:
                # If JSON parsing fails, create structured strategy
                marketing_strategy = {
                    "target_audience": "Primary target audience for the business",
                    "value_proposition": "Unique value proposition",
                    "content_strategy": {
                        "image_strategy": "Visual content approach",
                        "video_strategy": "Video content approach", 
                        "text_strategy": "Written content approach"
                    },
                    "competitive_positioning": "How to position against competitors",
                    "key_messaging": ["Key message 1", "Key message 2", "Key message 3"],
                    "campaign_objectives": ["Objective 1", "Objective 2", "Objective 3"],
                    "raw_ai_response": strategy_text
                }
            
            marketing_strategy['created_at'] = datetime.now().isoformat()
            marketing_strategy['business_context'] = business_context
            
            state.status_messages.append("Marketing strategy generated successfully")
            logger.info("Marketing strategy generated successfully")
            
            return marketing_strategy
            
        except Exception as e:
            logger.error(f"Marketing strategy generation failed: {str(e)}")
            raise Exception(f"Failed to generate marketing strategy: {str(e)}")
    
    async def _generate_content_prompts(self, marketing_strategy: Dict[str, Any], 
                                      state: CampaignState) -> Dict[str, Any]:
        """
        Generate specific JSON prompts for content creation using GPT-4o-mini
        """
        logger.info("Generating content prompts")
        state.status_messages.append("Creating content generation prompts")
        
        if not self.openai_client:
            raise Exception("OpenAI API key not configured")
        
        try:
            # Create prompt for generating content prompts
            prompt_generation_request = f"""
            Based on this marketing strategy, create specific JSON prompts for content generation:
            
            Strategy: {json.dumps(marketing_strategy, indent=2)}
            
            Generate detailed prompts for:
            1. Image content (3 different image concepts)
            2. Video content (2 different video concepts)  
            3. Text content (5 different text pieces for social media, ads, etc.)
            
            Return ONLY valid JSON in this exact format:
            {{
                "image_prompts": [
                    {{"id": "img_1", "title": "Image Title", "prompt": "Detailed DALL-E prompt", "style": "professional/creative/etc"}},
                    {{"id": "img_2", "title": "Image Title", "prompt": "Detailed DALL-E prompt", "style": "professional/creative/etc"}},
                    {{"id": "img_3", "title": "Image Title", "prompt": "Detailed DALL-E prompt", "style": "professional/creative/etc"}}
                ],
                "video_prompts": [
                    {{"id": "vid_1", "title": "Video Title", "prompt": "Detailed video generation prompt", "duration": "30s"}},
                    {{"id": "vid_2", "title": "Video Title", "prompt": "Detailed video generation prompt", "duration": "15s"}}
                ],
                "text_prompts": [
                    {{"id": "txt_1", "title": "Social Media Post", "prompt": "Create engaging social media content about...", "platform": "instagram"}},
                    {{"id": "txt_2", "title": "Ad Copy", "prompt": "Write compelling ad copy that...", "platform": "facebook"}},
                    {{"id": "txt_3", "title": "Email Subject", "prompt": "Generate email subject line for...", "platform": "email"}},
                    {{"id": "txt_4", "title": "Blog Title", "prompt": "Create blog post title about...", "platform": "blog"}},
                    {{"id": "txt_5", "title": "Product Description", "prompt": "Write product description that...", "platform": "website"}}
                ]
            }}
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a content strategist. Generate specific, actionable content prompts in valid JSON format only."},
                    {"role": "user", "content": prompt_generation_request}
                ],
                max_tokens=1500,
                temperature=0.8
            )
            
            prompts_text = response.choices[0].message.content
            
            # Parse JSON prompts
            try:
                content_prompts = json.loads(prompts_text)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON prompts: {e}")
                # Create fallback prompts structure
                content_prompts = self._create_fallback_prompts(marketing_strategy)
            
            content_prompts['generated_at'] = datetime.now().isoformat()
            content_prompts['source_strategy'] = marketing_strategy.get('campaign_objectives', [])
            
            state.status_messages.append(f"Generated {len(content_prompts.get('image_prompts', []))} image, {len(content_prompts.get('video_prompts', []))} video, and {len(content_prompts.get('text_prompts', []))} text prompts")
            logger.info("Content prompts generated successfully")
            
            return content_prompts
            
        except Exception as e:
            logger.error(f"Content prompt generation failed: {str(e)}")
            raise Exception(f"Failed to generate content prompts: {str(e)}")
    
    def _create_fallback_prompts(self, marketing_strategy: Dict[str, Any]) -> Dict[str, Any]:
        """Create fallback prompts if JSON parsing fails"""
        business_name = marketing_strategy.get('business_context', {}).get('business_name', 'Business')
        
        return {
            "image_prompts": [
                {"id": "img_1", "title": "Professional Brand Image", "prompt": f"Professional marketing image for {business_name}, modern design, high quality", "style": "professional"},
                {"id": "img_2", "title": "Social Media Visual", "prompt": f"Eye-catching social media graphic for {business_name}, engaging design", "style": "creative"},
                {"id": "img_3", "title": "Product Showcase", "prompt": f"Product showcase image for {business_name}, clean modern aesthetic", "style": "minimal"}
            ],
            "video_prompts": [
                {"id": "vid_1", "title": "Brand Introduction", "prompt": f"Create a 30-second brand introduction video for {business_name}", "duration": "30s"},
                {"id": "vid_2", "title": "Product Demo", "prompt": f"Create a 15-second product demonstration for {business_name}", "duration": "15s"}
            ],
            "text_prompts": [
                {"id": "txt_1", "title": "Social Media Post", "prompt": f"Create engaging social media content for {business_name}", "platform": "instagram"},
                {"id": "txt_2", "title": "Ad Copy", "prompt": f"Write compelling ad copy for {business_name}", "platform": "facebook"},
                {"id": "txt_3", "title": "Email Subject", "prompt": f"Generate email subject line for {business_name}", "platform": "email"},
                {"id": "txt_4", "title": "Blog Title", "prompt": f"Create blog post title for {business_name}", "platform": "blog"},
                {"id": "txt_5", "title": "Product Description", "prompt": f"Write product description for {business_name}", "platform": "website"}
            ]
        }
    
    async def _generate_ai_content(self, content_prompts: Dict[str, Any], 
                                 state: CampaignState) -> Dict[str, Any]:
        """
        Generate final AI content using appropriate APIs for each content type
        """
        logger.info("Starting AI content generation")
        state.status_messages.append("Generating final content with AI")
        
        generated_content = {
            'images': [],
            'videos': [],
            'texts': [],
            'generation_summary': {}
        }
        
        # Generate Images with DALL-E
        if self.openai_client and 'image_prompts' in content_prompts:
            images = await self._generate_images(content_prompts['image_prompts'])
            generated_content['images'] = images
        
        # Generate Videos with Google Veo3 (or fallback)
        if 'video_prompts' in content_prompts:
            videos = await self._generate_videos(content_prompts['video_prompts'])
            generated_content['videos'] = videos
        
        # Generate Text with GPT-4o-mini
        if self.openai_client and 'text_prompts' in content_prompts:
            texts = await self._generate_texts(content_prompts['text_prompts'])
            generated_content['texts'] = texts
        
        # Create generation summary
        generated_content['generation_summary'] = {
            'total_images': len(generated_content['images']),
            'total_videos': len(generated_content['videos']),
            'total_texts': len(generated_content['texts']),
            'generated_at': datetime.now().isoformat()
        }
        
        state.status_messages.append(f"Generated {len(generated_content['images'])} images, {len(generated_content['videos'])} videos, {len(generated_content['texts'])} text pieces")
        logger.info("AI content generation completed")
        
        return generated_content
    
    async def _generate_images(self, image_prompts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate images using DALL-E API"""
        logger.info(f"Generating {len(image_prompts)} images")
        images = []
        
        for prompt_data in image_prompts:
            try:
                response = self.openai_client.images.generate(
                    model="dall-e-3",
                    prompt=prompt_data['prompt'],
                    size="1024x1024",
                    quality="standard",
                    n=1
                )
                
                image_data = {
                    'id': prompt_data['id'],
                    'title': prompt_data['title'],
                    'url': response.data[0].url,
                    'prompt_used': prompt_data['prompt'],
                    'style': prompt_data.get('style', 'standard'),
                    'generated_at': datetime.now().isoformat()
                }
                images.append(image_data)
                logger.info(f"Generated image: {prompt_data['title']}")
                
            except Exception as e:
                logger.error(f"Image generation failed for {prompt_data['id']}: {str(e)}")
                # Add placeholder for failed generation
                images.append({
                    'id': prompt_data['id'],
                    'title': prompt_data['title'],
                    'error': str(e),
                    'status': 'failed'
                })
        
        return images
    
    async def _generate_videos(self, video_prompts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate videos using Google API (placeholder for Veo3)"""
        logger.info(f"Generating {len(video_prompts)} videos")
        videos = []
        
        for prompt_data in video_prompts:
            try:
                # Note: Google Veo3 is not yet available, using placeholder approach
                # In production, this would call the actual Google Veo3 API
                
                if self.google_client:
                    # For now, create a text description of what the video would be
                    description_prompt = f"Describe in detail what this video would look like: {prompt_data['prompt']}"
                    
                    # Using Google Gemini to create detailed video descriptions
                    # This would be replaced with actual Veo3 video generation when available
                    video_data = {
                        'id': prompt_data['id'],
                        'title': prompt_data['title'],
                        'description': f"Video concept: {prompt_data['prompt']}",
                        'duration': prompt_data.get('duration', '30s'),
                        'prompt_used': prompt_data['prompt'],
                        'status': 'concept_ready',  # Would be 'generated' with actual Veo3
                        'note': 'Video generation pending Veo3 API availability',
                        'generated_at': datetime.now().isoformat()
                    }
                    videos.append(video_data)
                    logger.info(f"Video concept created: {prompt_data['title']}")
                
            except Exception as e:
                logger.error(f"Video generation failed for {prompt_data['id']}: {str(e)}")
                videos.append({
                    'id': prompt_data['id'],
                    'title': prompt_data['title'],
                    'error': str(e),
                    'status': 'failed'
                })
        
        return videos
    
    async def _generate_texts(self, text_prompts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate text content using GPT-4o-mini"""
        logger.info(f"Generating {len(text_prompts)} text pieces")
        texts = []
        
        for prompt_data in text_prompts:
            try:
                response = self.openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": f"You are a marketing copywriter specializing in {prompt_data.get('platform', 'general')} content. Create engaging, conversion-focused content."},
                        {"role": "user", "content": prompt_data['prompt']}
                    ],
                    max_tokens=300,
                    temperature=0.8
                )
                
                text_data = {
                    'id': prompt_data['id'],
                    'title': prompt_data['title'],
                    'content': response.choices[0].message.content.strip(),
                    'platform': prompt_data.get('platform', 'general'),
                    'prompt_used': prompt_data['prompt'],
                    'generated_at': datetime.now().isoformat()
                }
                texts.append(text_data)
                logger.info(f"Generated text: {prompt_data['title']}")
                
            except Exception as e:
                logger.error(f"Text generation failed for {prompt_data['id']}: {str(e)}")
                texts.append({
                    'id': prompt_data['id'],
                    'title': prompt_data['title'],
                    'error': str(e),
                    'status': 'failed'
                })
        
        return texts
    
    async def _save_campaign_data(self, campaign_id: str, campaign_data: Dict[str, Any]) -> str:
        """Save campaign data to individual storage"""
        file_path = os.path.join(self.storage_dir, f"{campaign_id}.json")
        
        with open(file_path, 'w') as f:
            json.dump(campaign_data, f, indent=2)
        
        logger.info(f"Campaign data saved to: {file_path}")
        return file_path

# Initialize the campaign generator
campaign_generator = CampaignGenerator()

# Reflex State Class with Event Handlers
class CampaignState(CampaignState):
    """Extended state class with event handlers"""
    
    async def start_campaign_generation(self):
        """Start the campaign generation process"""
        if not self.url_input.strip():
            self.error_message = "Please enter a valid URL"
            return
        
        if not self.url_input.startswith(('http://', 'https://')):
            self.url_input = 'https://' + self.url_input
        
        try:
            # Reset state
            self.error_message = ""
            self.status_messages = []
            self.current_step = "Initializing"
            self.progress_percentage = 0
            
            # Start campaign generation
            async for _ in campaign_generator.generate_campaign(self.url_input, self):
                yield
                
        except Exception as e:
            self.error_message = f"Campaign generation failed: {str(e)}"
            self.is_processing = False
            logger.error(f"Campaign generation error: {str(e)}")
    
    def clear_results(self):
        """Clear all results and reset state"""
        self.url_input = ""
        self.is_processing = False
        self.current_step = ""
        self.progress_percentage = 0
        self.campaign_id = ""
        self.website_data = {}
        self.competitors = []
        self.marketing_strategy = {}
        self.content_prompts = {}
        self.generated_content = {}
        self.status_messages = []
        self.error_message = ""

def index() -> rx.Component:
    """Main Reflex frontend component"""
    return rx.vstack(
        # Header
        rx.heading("AI Campaign Generator", size="9", align="center"),
        rx.text("Enter a URL to generate a comprehensive marketing campaign", 
                size="5", align="center", color_scheme="gray"),
        
        rx.divider(),
        
        # URL Input Section
        rx.vstack(
            rx.heading("Enter Website URL", size="6"),
            rx.hstack(
                rx.input(
                    placeholder="https://example.com",
                    value=CampaignState.url_input,
                    on_change=CampaignState.set_url_input,
                    width="400px",
                    disabled=CampaignState.is_processing
                ),
                rx.button(
                    "Generate Campaign",
                    on_click=CampaignState.start_campaign_generation,
                    loading=CampaignState.is_processing,
                    disabled=CampaignState.is_processing,
                    color_scheme="blue"
                ),
                align="center"
            ),
            align="center",
            spacing="4"
        ),
        
        # Progress Section
        rx.cond(
            CampaignState.is_processing | (CampaignState.current_step != ""),
            rx.vstack(
                rx.divider(),
                rx.heading("Generation Progress", size="5"),
                rx.progress(value=CampaignState.progress_percentage),
                rx.text(f"Current Step: {CampaignState.current_step}"),
                rx.text(f"Progress: {CampaignState.progress_percentage}%"),
                
                # Status Messages
                rx.cond(
                    CampaignState.status_messages,
                    rx.vstack(
                        rx.heading("Status Updates", size="4"),
                        rx.foreach(
                            CampaignState.status_messages,
                            lambda message: rx.text(f"• {message}", size="2")
                        ),
                        align="start",
                        width="100%"
                    )
                ),
                
                width="100%",
                align="center"
            )
        ),
        
        # Error Section
        rx.cond(
            CampaignState.error_message != "",
            rx.vstack(
                rx.divider(),
                rx.callout(
                    CampaignState.error_message,
                    icon="triangle_alert",
                    color_scheme="red",
                    role="alert"
                ),
                align="center"
            )
        ),
        
        # Results Section
        rx.cond(
            CampaignState.generated_content != {},
            rx.vstack(
                rx.divider(),
                rx.heading("Generated Campaign Content", size="6"),
                
                # Campaign Summary
                rx.card(
                    rx.vstack(
                        rx.heading("Campaign Summary", size="4"),
                        rx.text(f"Campaign ID: {CampaignState.campaign_id}"),
                        rx.text(f"Business: {CampaignState.website_data.get('business_name', 'N/A')}"),
                        rx.text(f"Generated Images: {len(CampaignState.generated_content.get('images', []))}"),
                        rx.text(f"Generated Videos: {len(CampaignState.generated_content.get('videos', []))}"),
                        rx.text(f"Generated Texts: {len(CampaignState.generated_content.get('texts', []))}"),
                        align="start"
                    ),
                    width="100%"
                ),
                
                # Generated Images
                rx.cond(
                    CampaignState.generated_content.get('images', []),
                    rx.card(
                        rx.vstack(
                            rx.heading("Generated Images", size="4"),
                            rx.foreach(
                                CampaignState.generated_content.get('images', []),
                                lambda img: rx.vstack(
                                    rx.heading(img.get('title', 'Untitled'), size="3"),
                                    rx.cond(
                                        img.get('url'),
                                        rx.image(src=img.get('url'), width="300px", height="300px"),
                                        rx.text(f"Error: {img.get('error', 'Generation failed')}", color="red")
                                    ),
                                    rx.text(f"Style: {img.get('style', 'N/A')}", size="2"),
                                    align="center",
                                    spacing="2"
                                )
                            ),
                            align="center"
                        ),
                        width="100%"
                    )
                ),
                
                # Generated Videos
                rx.cond(
                    CampaignState.generated_content.get('videos', []),
                    rx.card(
                        rx.vstack(
                            rx.heading("Generated Videos", size="4"),
                            rx.foreach(
                                CampaignState.generated_content.get('videos', []),
                                lambda vid: rx.vstack(
                                    rx.heading(vid.get('title', 'Untitled'), size="3"),
                                    rx.text(vid.get('description', 'No description')),
                                    rx.text(f"Duration: {vid.get('duration', 'N/A')}", size="2"),
                                    rx.text(f"Status: {vid.get('status', 'Unknown')}", size="2"),
                                    align="start",
                                    spacing="2"
                                )
                            ),
                            align="center"
                        ),
                        width="100%"
                    )
                ),
                
                # Generated Text Content
                rx.cond(
                    CampaignState.generated_content.get('texts', []),
                    rx.card(
                        rx.vstack(
                            rx.heading("Generated Text Content", size="4"),
                            rx.foreach(
                                CampaignState.generated_content.get('texts', []),
                                lambda txt: rx.card(
                                    rx.vstack(
                                        rx.heading(txt.get('title', 'Untitled'), size="3"),
                                        rx.text(txt.get('content', 'No content'), size="2"),
                                        rx.text(f"Platform: {txt.get('platform', 'N/A')}", size="1", color="gray"),
                                        align="start",
                                        spacing="2"
                                    ),
                                    width="100%"
                                )
                            ),
                            align="center",
                            spacing="3"
                        ),
                        width="100%"
                    )
                ),
                
                # Clear Results Button
                rx.button(
                    "Start New Campaign",
                    on_click=CampaignState.clear_results,
                    color_scheme="gray",
                    variant="outline"
                ),
                
                width="100%",
                align="center",
                spacing="6"
            )
        ),
        
        spacing="6",
        align="center",
        min_height="100vh",
        padding="4"
    )

# Create the Reflex app
app = rx.App()
app.add_page(index)