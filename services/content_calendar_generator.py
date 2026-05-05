"""
Content Calendar Generator - Creates comprehensive content calendars with hooks, timing, and variations
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import random

class ContentCalendarGenerator:
    """
    Generates comprehensive content calendars following the protocol requirements
    """
    
    CONTENT_TYPES = [
        'social_post', 'video_content', 'blog_post', 'story_content', 
        'educational_content', 'testimonial', 'behind_scenes', 'promotional'
    ]
    
    PLATFORMS = ['facebook', 'instagram', 'youtube', 'linkedin', 'tiktok', 'google_my_business']
    
    OPTIMAL_TIMES = {
        'facebook': ['9:00 AM', '1:00 PM', '3:00 PM'],
        'instagram': ['11:00 AM', '2:00 PM', '5:00 PM'],
        'youtube': ['2:00 PM', '8:00 PM'],
        'linkedin': ['8:00 AM', '12:00 PM', '5:00 PM'],
        'tiktok': ['6:00 AM', '10:00 AM', '7:00 PM'],
        'google_my_business': ['10:00 AM', '2:00 PM', '6:00 PM']
    }
    
    def __init__(self):
        pass
    
    async def generate_calendar(self, duration_days: int = 30, tone: str = 'professional', 
                              trends: List[str] = None, competitive_gaps: Dict[str, Any] = None,
                              business_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate comprehensive content calendar
        """
        try:
            calendar_data = {
                'generation_timestamp': datetime.utcnow().isoformat(),
                'duration_days': duration_days,
                'tone': tone,
                'calendar_entries': [],
                'content_themes': [],
                'posting_schedule': {},
                'utm_tracking': {},
                'ab_test_plan': {}
            }
            
            # Generate calendar entries
            start_date = datetime.now()
            
            for day in range(duration_days):
                current_date = start_date + timedelta(days=day)
                
                # Generate content for this day
                daily_content = await self._generate_daily_content(
                    current_date, tone, trends or [], competitive_gaps or {}, business_info or {}
                )
                
                calendar_data['calendar_entries'].extend(daily_content)
            
            # Generate content themes
            calendar_data['content_themes'] = self._generate_content_themes(tone, trends, business_info)
            
            # Create posting schedule
            calendar_data['posting_schedule'] = self._create_posting_schedule(calendar_data['calendar_entries'])
            
            # Generate UTM tracking plan
            calendar_data['utm_tracking'] = self._generate_utm_plan(calendar_data['calendar_entries'])
            
            # Create A/B test plan
            calendar_data['ab_test_plan'] = self._create_ab_test_plan(calendar_data['calendar_entries'], tone)
            
            return calendar_data
            
        except Exception as e:
            logging.error(f"Content calendar generation failed: {e}")
            return {'error': str(e)}
    
    async def _generate_daily_content(self, date: datetime, tone: str, trends: List[str], 
                                    competitive_gaps: Dict[str, Any], business_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate content for a specific day"""
        daily_content = []
        
        try:
            # Determine content frequency based on day of week
            day_of_week = date.weekday()  # 0 = Monday, 6 = Sunday
            
            # Higher frequency on weekdays
            content_count = 2 if day_of_week < 5 else 1
            
            for i in range(content_count):
                content_entry = {
                    'date': date.strftime('%Y-%m-%d'),
                    'day_of_week': date.strftime('%A'),
                    'content_id': f"{date.strftime('%Y%m%d')}_{i+1}",
                    'content_type': self._select_content_type(day_of_week, i),
                    'platform': self._select_platform(day_of_week, i),
                    'timing': self._select_optimal_time(day_of_week, i),
                    'hook': self._generate_hook(tone, trends, competitive_gaps),
                    'topic': self._generate_topic(trends, competitive_gaps, business_info),
                    'caption': '',  # Will be filled by content generator
                    'hashtags': self._generate_hashtags(trends, business_info),
                    'cta': self._generate_cta(tone),
                    'visual_direction': self._generate_visual_direction(tone),
                    'utm_parameters': {},
                    'ab_variation': 'A'  # Default variation
                }
                
                # Generate full caption
                content_entry['caption'] = self._generate_caption(content_entry, tone)
                
                # Add UTM parameters
                content_entry['utm_parameters'] = self._generate_utm_parameters(content_entry)
                
                daily_content.append(content_entry)
                
        except Exception as e:
            logging.warning(f"Daily content generation failed for {date}: {e}")
        
        return daily_content
    
    def _select_content_type(self, day_of_week: int, content_index: int) -> str:
        """Select content type based on day and posting sequence"""
        
        # Content type strategy by day
        weekday_strategy = {
            0: ['educational_content', 'social_post'],  # Monday
            1: ['behind_scenes', 'testimonial'],        # Tuesday
            2: ['video_content', 'social_post'],        # Wednesday
            3: ['educational_content', 'promotional'],   # Thursday
            4: ['testimonial', 'social_post'],          # Friday
            5: ['behind_scenes', 'story_content'],      # Saturday
            6: ['social_post', 'video_content']         # Sunday
        }
        
        day_types = weekday_strategy.get(day_of_week, ['social_post', 'educational_content'])
        return day_types[content_index % len(day_types)]
    
    def _select_platform(self, day_of_week: int, content_index: int) -> str:
        """Select platform based on optimal engagement patterns"""
        
        # Platform strategy by day
        platform_strategy = {
            0: ['linkedin', 'facebook'],      # Monday - Professional start
            1: ['instagram', 'facebook'],     # Tuesday - Visual content
            2: ['youtube', 'linkedin'],       # Wednesday - Long-form content
            3: ['facebook', 'instagram'],     # Thursday - Engagement focus
            4: ['instagram', 'tiktok'],       # Friday - Social/fun content
            5: ['instagram', 'facebook'],     # Saturday - Lifestyle content
            6: ['youtube', 'instagram']       # Sunday - Inspirational content
        }
        
        day_platforms = platform_strategy.get(day_of_week, ['facebook', 'instagram'])
        return day_platforms[content_index % len(day_platforms)]
    
    def _select_optimal_time(self, day_of_week: int, content_index: int) -> str:
        """Select optimal posting time"""
        
        # Time strategy by day
        if day_of_week < 5:  # Weekdays
            times = ['9:00 AM', '1:00 PM', '5:00 PM']
        else:  # Weekends
            times = ['10:00 AM', '2:00 PM', '7:00 PM']
        
        return times[content_index % len(times)]
    
    def _generate_hook(self, tone: str, trends: List[str], competitive_gaps: Dict[str, Any]) -> str:
        """Generate attention-grabbing hooks based on tone"""
        
        # Tone-specific hook templates
        hook_templates = {
            'professional': [
                "Industry insight: {trend}",
                "Expert tip: {topic}",
                "Professional perspective on {trend}"
            ],
            'educational': [
                "Did you know: {fact}",
                "Learn how to {action}",
                "The complete guide to {topic}"
            ],
            'edgy': [
                "What they don't tell you about {topic}",
                "The uncomfortable truth about {trend}",
                "Industry secret: {insight}"
            ],
            'roast': [
                "While our competitors are busy {doing_wrong}...",
                "What happens when you choose {competitor_mistake}",
                "The difference between us and 'the other guys'"
            ],
            'funny': [
                "When {situation} happens...",
                "That awkward moment when {scenario}",
                "POV: You {funny_situation}"
            ],
            'joyful': [
                "Celebrating {achievement}!",
                "Amazing news about {topic}!",
                "We're thrilled to share {update}"
            ]
        }
        
        templates = hook_templates.get(tone, hook_templates['professional'])
        template = random.choice(templates)
        
        # Fill template with relevant content
        if '{trend}' in template and trends:
            return template.replace('{trend}', random.choice(trends))
        elif '{topic}' in template:
            return template.replace('{topic}', 'quality service')
        else:
            return template
    
    def _generate_topic(self, trends: List[str], competitive_gaps: Dict[str, Any], 
                       business_info: Dict[str, Any]) -> str:
        """Generate content topic"""
        
        # Topic sources in priority order
        topic_sources = []
        
        # Add trending topics
        if trends:
            topic_sources.extend([f"Trending: {trend}" for trend in trends[:3]])
        
        # Add competitive gap topics
        if competitive_gaps.get('untapped_topics'):
            topic_sources.extend([f"Opportunity: {topic}" for topic in competitive_gaps['untapped_topics'][:2]])
        
        # Add business service topics
        if business_info.get('services'):
            topic_sources.extend([f"Service focus: {service}" for service in business_info['services'][:3]])
        
        # Default topics
        if not topic_sources:
            topic_sources = [
                'Quality craftsmanship',
                'Customer satisfaction',
                'Local community service',
                'Industry expertise',
                'Project showcase'
            ]
        
        return random.choice(topic_sources)
    
    def _generate_hashtags(self, trends: List[str], business_info: Dict[str, Any]) -> List[str]:
        """Generate relevant hashtags"""
        hashtags = []
        
        # Business-specific hashtags
        if business_info.get('services'):
            for service in business_info['services'][:2]:
                hashtag = '#' + service.replace(' ', '').lower()
                hashtags.append(hashtag)
        
        # Trending hashtags
        if trends:
            for trend in trends[:2]:
                hashtag = '#' + trend.replace(' ', '').lower()
                hashtags.append(hashtag)
        
        # Generic business hashtags
        generic_hashtags = [
            '#local', '#quality', '#professional', '#trusted', 
            '#experienced', '#customer', '#service', '#community'
        ]
        
        hashtags.extend(random.sample(generic_hashtags, 3))
        
        return hashtags[:8]  # Limit to 8 hashtags
    
    def _generate_cta(self, tone: str) -> str:
        """Generate call-to-action based on tone"""
        
        cta_by_tone = {
            'professional': [
                'Contact us for a consultation',
                'Schedule your appointment today',
                'Get your professional quote'
            ],
            'edgy': [
                'Ready to see the difference?',
                'Don\'t settle for mediocre',
                'Experience the upgrade'
            ],
            'roast': [
                'Choose quality over cheap',
                'Get it done right the first time',
                'See why we\'re different'
            ],
            'educational': [
                'Learn more in our guide',
                'Get expert tips',
                'Download our free resource'
            ],
            'joyful': [
                'Join our happy customers!',
                'Let\'s create something amazing!',
                'Start your journey with us!'
            ]
        }
        
        ctas = cta_by_tone.get(tone, cta_by_tone['professional'])
        return random.choice(ctas)
    
    def _generate_visual_direction(self, tone: str) -> Dict[str, Any]:
        """Generate visual content direction"""
        
        visual_styles = {
            'professional': {
                'style': 'clean_professional',
                'colors': ['navy', 'white', 'gray'],
                'elements': ['clean_typography', 'minimal_design', 'professional_photos']
            },
            'edgy': {
                'style': 'bold_modern',
                'colors': ['black', 'red', 'white'],
                'elements': ['bold_typography', 'high_contrast', 'dramatic_angles']
            },
            'educational': {
                'style': 'informative_clear',
                'colors': ['blue', 'white', 'orange'],
                'elements': ['infographics', 'step_by_step', 'clear_text']
            },
            'joyful': {
                'style': 'bright_cheerful',
                'colors': ['yellow', 'blue', 'green'],
                'elements': ['bright_photos', 'happy_people', 'celebratory']
            }
        }
        
        return visual_styles.get(tone, visual_styles['professional'])
    
    def _generate_caption(self, content_entry: Dict[str, Any], tone: str) -> str:
        """Generate full caption for content"""
        
        hook = content_entry['hook']
        topic = content_entry['topic']
        cta = content_entry['cta']
        hashtags = ' '.join(content_entry['hashtags'])
        
        # Caption structure: Hook + Body + CTA + Hashtags
        body_templates = {
            'professional': "Our team brings years of experience to every project. We're committed to delivering quality results that exceed expectations.",
            'educational': "Here's what you need to know about this topic. Understanding these key points will help you make informed decisions.",
            'edgy': "The truth is, most people don't know this. We're here to change that and give you the real information.",
            'joyful': "We absolutely love what we do! Every project is an opportunity to create something amazing with our clients."
        }
        
        body = body_templates.get(tone, body_templates['professional'])
        
        caption = f"{hook}\n\n{body}\n\n{cta}\n\n{hashtags}"
        
        return caption
    
    def _generate_utm_parameters(self, content_entry: Dict[str, Any]) -> Dict[str, str]:
        """Generate UTM parameters for tracking"""
        
        return {
            'utm_source': content_entry['platform'],
            'utm_medium': 'social',
            'utm_campaign': f"content_{content_entry['date'].replace('-', '')}",
            'utm_content': f"{content_entry['content_type']}_{content_entry['content_id']}",
            'utm_term': content_entry['topic'].replace(' ', '_').lower()
        }
    
    def _generate_content_themes(self, tone: str, trends: List[str], 
                               business_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate recurring content themes"""
        
        themes = [
            {
                'theme_name': 'Monday Motivation',
                'frequency': 'weekly',
                'content_type': 'inspirational',
                'description': 'Start the week with motivational content'
            },
            {
                'theme_name': 'Tip Tuesday',
                'frequency': 'weekly',
                'content_type': 'educational',
                'description': 'Share helpful tips and advice'
            },
            {
                'theme_name': 'Work Wednesday',
                'frequency': 'weekly',
                'content_type': 'behind_scenes',
                'description': 'Show behind-the-scenes work content'
            },
            {
                'theme_name': 'Testimonial Thursday',
                'frequency': 'weekly',
                'content_type': 'testimonial',
                'description': 'Feature customer testimonials and reviews'
            },
            {
                'theme_name': 'Feature Friday',
                'frequency': 'weekly',
                'content_type': 'promotional',
                'description': 'Highlight services and special offers'
            }
        ]
        
        return themes
    
    def _create_posting_schedule(self, calendar_entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create posting schedule summary"""
        
        schedule = {
            'total_posts': len(calendar_entries),
            'posts_per_week': len(calendar_entries) // 4.3,  # Approximate weeks in month
            'platform_distribution': {},
            'content_type_distribution': {},
            'optimal_times': {}
        }
        
        # Calculate distributions
        for entry in calendar_entries:
            platform = entry['platform']
            content_type = entry['content_type']
            timing = entry['timing']
            
            schedule['platform_distribution'][platform] = schedule['platform_distribution'].get(platform, 0) + 1
            schedule['content_type_distribution'][content_type] = schedule['content_type_distribution'].get(content_type, 0) + 1
            schedule['optimal_times'][timing] = schedule['optimal_times'].get(timing, 0) + 1
        
        return schedule
    
    def _generate_utm_plan(self, calendar_entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate comprehensive UTM tracking plan"""
        
        utm_plan = {
            'tracking_strategy': 'comprehensive_content_tracking',
            'parameter_structure': {
                'utm_source': 'Social platform (facebook, instagram, etc.)',
                'utm_medium': 'Always "social" for social media content',
                'utm_campaign': 'Date-based campaign identifier',
                'utm_content': 'Specific content piece identifier',
                'utm_term': 'Topic or keyword focus'
            },
            'reporting_dimensions': [
                'platform_performance',
                'content_type_effectiveness',
                'timing_optimization',
                'topic_engagement'
            ],
            'success_metrics': [
                'click_through_rate',
                'engagement_rate',
                'conversion_rate',
                'cost_per_engagement'
            ]
        }
        
        return utm_plan
    
    def _create_ab_test_plan(self, calendar_entries: List[Dict[str, Any]], tone: str) -> Dict[str, Any]:
        """Create A/B testing plan for content"""
        
        ab_plan = {
            'test_strategy': 'systematic_content_optimization',
            'test_variables': [
                'hook_variations',
                'cta_variations',
                'visual_styles',
                'posting_times',
                'caption_length'
            ],
            'test_schedule': {
                'weekly_tests': 2,
                'test_duration': '7_days',
                'sample_size': 'minimum_100_per_variation'
            },
            'success_criteria': {
                'primary_metric': 'engagement_rate',
                'secondary_metrics': ['click_through_rate', 'reach', 'saves'],
                'significance_threshold': '95%'
            },
            'planned_tests': []
        }
        
        # Generate specific A/B tests
        test_concepts = [
            {
                'test_name': 'Hook Style Comparison',
                'variable': 'hook_approach',
                'variation_a': f'{tone} tone with question format',
                'variation_b': f'{tone} tone with statement format',
                'hypothesis': 'Question format will drive higher engagement'
            },
            {
                'test_name': 'CTA Urgency Test',
                'variable': 'cta_urgency',
                'variation_a': 'Low urgency CTA',
                'variation_b': 'High urgency CTA',
                'hypothesis': 'Higher urgency will improve click-through rate'
            },
            {
                'test_name': 'Visual Style Test',
                'variable': 'visual_approach',
                'variation_a': 'Product/service focused visuals',
                'variation_b': 'People/lifestyle focused visuals',
                'hypothesis': 'People-focused visuals will increase relatability'
            }
        ]
        
        ab_plan['planned_tests'] = test_concepts
        
        return ab_plan