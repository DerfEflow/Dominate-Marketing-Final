"""
Main Reflex application for AI Campaign Generator
Integrates all modules for comprehensive campaign generation
"""

import reflex as rx
import os
import asyncio
import uuid
import json
from datetime import datetime
from typing import Dict, List, Any

# Import our modules
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'modules'))

from web_scraper import ReliableWebScraper
from competitor_analyzer import CompetitorAnalyzer  
from ai_strategy_generator import AIStrategyGenerator
from content_generator import ContentGenerator

class CampaignState(rx.State):
    """Main state for campaign generation"""
    
    # Input
    url_input: str = ""
    
    # Process control
    is_processing: bool = False
    current_step: str = ""
    progress: int = 0
    
    # Campaign data
    campaign_id: str = ""
    business_data: Dict[str, Any] = {}
    competitor_data: List[Dict[str, Any]] = []
    marketing_strategy: Dict[str, Any] = {}
    content_prompts: Dict[str, Any] = {}
    generated_content: Dict[str, Any] = {}
    
    # Status and errors
    status_messages: List[str] = []
    error_message: str = ""
    
    async def generate_campaign(self):
        """Main campaign generation workflow"""
        if not self.url_input.strip():
            self.error_message = "Please enter a valid URL"
            return
        
        # Validate and format URL
        url = self.url_input.strip()
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        try:
            # Initialize
            self.campaign_id = str(uuid.uuid4())
            self.is_processing = True
            self.error_message = ""
            self.status_messages = []
            self.progress = 0
            
            # Step 1: Web Scraping
            self.current_step = "Extracting business data from website"
            self.progress = 20
            yield
            
            scraper = ReliableWebScraper()
            self.business_data = scraper.extract_business_data(url)
            self.status_messages.append(f"Extracted {self.business_data.get('content_length', 0)} characters from {self.business_data.get('business_name', 'website')}")
            
            # Step 2: Competitor Analysis
            self.current_step = "Finding and analyzing competitors"
            self.progress = 40
            yield
            
            # Check for API keys
            google_api_key = os.environ.get('GOOGLE_SEARCH_API_KEY')
            google_engine_id = os.environ.get('GOOGLE_SEARCH_ENGINE_ID')
            
            if google_api_key and google_engine_id:
                competitor_analyzer = CompetitorAnalyzer(google_api_key, google_engine_id)
                self.competitor_data = competitor_analyzer.find_competitors(self.business_data)
                self.status_messages.append(f"Found {len(self.competitor_data)} competitors")
            else:
                self.status_messages.append("Google Search API not configured - skipping competitor analysis")
                self.competitor_data = []
            
            # Step 3: AI Strategy Generation
            self.current_step = "Generating marketing strategy with AI"
            self.progress = 60
            yield
            
            strategy_generator = AIStrategyGenerator()
            self.marketing_strategy = strategy_generator.generate_marketing_strategy(
                self.business_data, self.competitor_data
            )
            self.status_messages.append("Marketing strategy generated")
            
            # Step 4: Content Prompts
            self.current_step = "Creating content generation prompts"
            self.progress = 80
            yield
            
            self.content_prompts = strategy_generator.generate_content_prompts(self.marketing_strategy)
            prompt_counts = {
                'images': len(self.content_prompts.get('image_prompts', [])),
                'videos': len(self.content_prompts.get('video_prompts', [])),
                'texts': len(self.content_prompts.get('text_prompts', []))
            }
            self.status_messages.append(f"Generated {prompt_counts['images']} image, {prompt_counts['videos']} video, {prompt_counts['texts']} text prompts")
            
            # Step 5: Content Generation
            self.current_step = "Generating final content with AI"
            self.progress = 95
            yield
            
            content_generator = ContentGenerator()
            self.generated_content = content_generator.generate_all_content(self.content_prompts)
            
            summary = self.generated_content.get('generation_summary', {})
            self.status_messages.append(f"Generated {summary.get('total_images', 0)} images, {summary.get('total_videos', 0)} videos, {summary.get('total_texts', 0)} texts")
            
            # Complete
            self.current_step = "Campaign generation complete"
            self.progress = 100
            self.is_processing = False
            
        except Exception as e:
            self.error_message = f"Campaign generation failed: {str(e)}"
            self.is_processing = False
            self.progress = 0
    
    def clear_results(self):
        """Clear all results and reset state"""
        self.url_input = ""
        self.is_processing = False
        self.current_step = ""
        self.progress = 0
        self.campaign_id = ""
        self.business_data = {}
        self.competitor_data = []
        self.marketing_strategy = {}
        self.content_prompts = {}
        self.generated_content = {}
        self.status_messages = []
        self.error_message = ""

def index() -> rx.Component:
    """Main page component"""
    return rx.container(
        rx.vstack(
            # Header
            rx.heading("AI Campaign Generator", size="9", text_align="center"),
            rx.text(
                "Enter any business website URL to generate a complete AI-powered marketing campaign",
                size="4",
                text_align="center",
                color="gray.600"
            ),
            
            # URL Input Section  
            rx.card(
                rx.vstack(
                    rx.heading("Website URL", size="5"),
                    rx.hstack(
                        rx.input(
                            placeholder="https://example.com",
                            value=CampaignState.url_input,
                            on_change=CampaignState.set_url_input,
                            size="3",
                            width="400px"
                        ),
                        rx.button(
                            "Generate Campaign",
                            on_click=CampaignState.generate_campaign,
                            loading=CampaignState.is_processing,
                            size="3",
                            color_scheme="blue"
                        ),
                        align="center"
                    ),
                    spacing="3",
                    align="center"
                ),
                width="100%"
            ),
            
            # Progress Section
            rx.cond(
                CampaignState.is_processing | (CampaignState.current_step != ""),
                rx.card(
                    rx.vstack(
                        rx.heading("Progress", size="4"),
                        rx.progress(value=CampaignState.progress, width="100%"),
                        rx.text(f"{CampaignState.progress}% - {CampaignState.current_step}"),
                        
                        # Status messages
                        rx.cond(
                            CampaignState.status_messages,
                            rx.vstack(
                                rx.text("Status Updates:", weight="bold"),
                                rx.foreach(
                                    CampaignState.status_messages,
                                    lambda msg: rx.text(f"• {msg}", size="2")
                                ),
                                align="start",
                                width="100%"
                            )
                        ),
                        
                        spacing="3",
                        align="center",
                        width="100%"
                    ),
                    width="100%"
                )
            ),
            
            # Error Display
            rx.cond(
                CampaignState.error_message != "",
                rx.callout(
                    CampaignState.error_message,
                    icon="triangle-alert",
                    color_scheme="red",
                    role="alert"
                )
            ),
            
            # Results Section
            rx.cond(
                CampaignState.generated_content != {},
                rx.vstack(
                    # Campaign Overview
                    rx.card(
                        rx.vstack(
                            rx.heading("Campaign Overview", size="5"),
                            rx.grid(
                                rx.vstack(
                                    rx.text("Business", weight="bold"),
                                    rx.text(CampaignState.business_data.get("business_name", "N/A"))
                                ),
                                rx.vstack(
                                    rx.text("Industry", weight="bold"),
                                    rx.text(CampaignState.business_data.get("industry", "N/A"))
                                ),
                                rx.vstack(
                                    rx.text("Content Extracted", weight="bold"),
                                    rx.text(f"{CampaignState.business_data.get('content_length', 0)} chars")
                                ),
                                rx.vstack(
                                    rx.text("Competitors Found", weight="bold"),
                                    rx.text(str(len(CampaignState.competitor_data)))
                                ),
                                columns="4",
                                spacing="4",
                                width="100%"
                            ),
                            spacing="3",
                            align="start",
                            width="100%"
                        ),
                        width="100%"
                    ),
                    
                    # Generated Images
                    rx.cond(
                        CampaignState.generated_content.get("images", []),
                        rx.card(
                            rx.vstack(
                                rx.heading("Generated Images", size="4"),
                                rx.grid(
                                    rx.foreach(
                                        CampaignState.generated_content.get("images", []),
                                        lambda img: rx.cond(
                                            img.get("status") == "success",
                                            rx.vstack(
                                                rx.image(
                                                    src=img.get("url", ""),
                                                    width="300px",
                                                    height="300px",
                                                    object_fit="cover"
                                                ),
                                                rx.text(img.get("title", "Untitled"), weight="bold"),
                                                rx.text(f"Style: {img.get('style', 'N/A')}", size="2"),
                                                align="center",
                                                spacing="2"
                                            ),
                                            rx.vstack(
                                                rx.text(img.get("title", "Failed"), weight="bold"),
                                                rx.text(f"Error: {img.get('error', 'Unknown')}", color="red"),
                                                align="center",
                                                spacing="2"
                                            )
                                        )
                                    ),
                                    columns="3",
                                    spacing="4"
                                ),
                                spacing="3",
                                align="center",
                                width="100%"
                            ),
                            width="100%"
                        )
                    ),
                    
                    # Generated Videos  
                    rx.cond(
                        CampaignState.generated_content.get("videos", []),
                        rx.card(
                            rx.vstack(
                                rx.heading("Generated Videos", size="4"),
                                rx.foreach(
                                    CampaignState.generated_content.get("videos", []),
                                    lambda vid: rx.card(
                                        rx.vstack(
                                            rx.text(vid.get("title", "Untitled"), weight="bold"),
                                            rx.text(vid.get("concept", vid.get("prompt_used", "No concept"))),
                                            rx.hstack(
                                                rx.text(f"Duration: {vid.get('duration', 'N/A')}", size="2"),
                                                rx.text(f"Status: {vid.get('status', 'Unknown')}", size="2"),
                                                spacing="4"
                                            ),
                                            align="start",
                                            spacing="2",
                                            width="100%"
                                        ),
                                        width="100%"
                                    )
                                ),
                                spacing="3",
                                align="center",
                                width="100%"
                            ),
                            width="100%"
                        )
                    ),
                    
                    # Generated Text Content
                    rx.cond(
                        CampaignState.generated_content.get("texts", []),
                        rx.card(
                            rx.vstack(
                                rx.heading("Generated Text Content", size="4"),
                                rx.foreach(
                                    CampaignState.generated_content.get("texts", []),
                                    lambda txt: rx.card(
                                        rx.vstack(
                                            rx.hstack(
                                                rx.text(txt.get("title", "Untitled"), weight="bold"),
                                                rx.badge(txt.get("platform", "general"), variant="soft"),
                                                justify="between",
                                                width="100%"
                                            ),
                                            rx.cond(
                                                txt.get("status") == "success",
                                                rx.text(txt.get("content", "No content")),
                                                rx.text(f"Error: {txt.get('error', 'Unknown')}", color="red")
                                            ),
                                            rx.text(f"Words: {txt.get('word_count', 0)} | Tone: {txt.get('tone', 'N/A')}", size="2", color="gray"),
                                            align="start",
                                            spacing="2",
                                            width="100%"
                                        ),
                                        width="100%"
                                    )
                                ),
                                spacing="3",
                                width="100%"
                            ),
                            width="100%"
                        )
                    ),
                    
                    # Clear button
                    rx.button(
                        "Generate New Campaign",
                        on_click=CampaignState.clear_results,
                        variant="outline",
                        size="3"
                    ),
                    
                    spacing="6",
                    width="100%"
                )
            ),
            
            spacing="6",
            align="center",
            width="100%"
        ),
        max_width="1200px",
        padding="4"
    )

# Create the app
app = rx.App(
    theme=rx.theme(
        appearance="dark",
        accent_color="blue"
    )
)
app.add_page(index)