# Campaign Generator Module

A comprehensive AI-powered marketing campaign generator built with Reflex framework. This module handles the complete workflow from URL input to final content generation.

## Features

- **Website Data Scraping**: Extracts business information and metadata from any URL
- **Competitive Analysis**: Finds top 5 competitors using Google Search API
- **AI Marketing Strategy**: Creates comprehensive marketing strategies using GPT-4o-mini
- **Content Prompt Generation**: Generates specific JSON prompts for different content types
- **Multi-Modal Content Creation**: 
  - Images via DALL-E 3
  - Videos via Google APIs (Veo3 ready)
  - Text content via GPT-4o-mini
- **Individual Campaign Storage**: Each campaign saved with unique ID

## Architecture

### Core Components

1. **CampaignGenerator Class**: Main orchestrator handling the complete workflow
2. **CampaignState Class**: Reflex state management with progress tracking
3. **API Integrations**: OpenAI, Google Search, Google Gemini/Veo3
4. **Storage System**: JSON-based campaign storage in individual files

### Workflow Steps

1. URL Input & Validation
2. Website Data Scraping (reading mode content + metadata)
3. Competitive Analysis (Google Search API)
4. Marketing Strategy Generation (GPT-4o-mini)
5. Content Prompt Generation (JSON format via GPT-4o-mini)
6. AI Content Generation:
   - Images: DALL-E 3
   - Videos: Google Veo3 (placeholder ready)
   - Text: GPT-4o-mini
7. Campaign Storage (individual JSON files)

## API Requirements

### Required APIs
- **OpenAI API**: Text generation (GPT-4o-mini) and image generation (DALL-E 3)
- **Google API**: For Gemini and future Veo3 video generation

### Optional APIs
- **Google Search API**: For competitor analysis (falls back to mock data if unavailable)

## Installation & Setup

### 1. Install Dependencies
```bash
pip install reflex>=0.6.0 openai>=1.0.0 google-genai>=0.7.0 trafilatura>=2.0.0 beautifulsoup4>=4.12.0 requests>=2.32.0
```

### 2. Configure API Keys
Copy `.env.example` to `.env` and add your API keys:

```bash
OPENAI_API_KEY=sk-your-openai-api-key-here
GOOGLE_API_KEY=your-google-api-key-here
GOOGLE_SEARCH_API_KEY=your-google-search-api-key-here  # Optional
GOOGLE_SEARCH_ENGINE_ID=your-search-engine-id-here    # Optional
```

### 3. Run the Application

#### Option 1: Full Reflex App
```bash
cd campaign_generator
reflex run
```

#### Option 2: Test Core Functionality
```bash
cd campaign_generator
python test_campaign_generator.py
```

## Usage

### Web Interface
1. Enter any website URL (e.g., https://example.com)
2. Click "Generate Campaign" 
3. Monitor real-time progress updates
4. View generated content:
   - Marketing strategy
   - Generated images with DALL-E
   - Video concepts (Veo3 ready)
   - Text content for multiple platforms

### Programmatic Usage
```python
from campaign_generator import CampaignGenerator, CampaignState

# Initialize
generator = CampaignGenerator()
state = CampaignState()

# Generate campaign
async for _ in generator.generate_campaign("https://example.com", state):
    print(f"Progress: {state.progress_percentage}%")

# Access results
print(f"Generated {len(state.generated_content['images'])} images")
print(f"Generated {len(state.generated_content['texts'])} text pieces")
```

## Generated Content Structure

### Images
```json
{
  "id": "img_1",
  "title": "Professional Brand Image",
  "url": "https://dalle-generated-image-url.com",
  "prompt_used": "Professional marketing image...",
  "style": "professional",
  "generated_at": "2025-08-08T19:00:00"
}
```

### Videos
```json
{
  "id": "vid_1", 
  "title": "Brand Introduction",
  "description": "30-second brand introduction video",
  "duration": "30s",
  "status": "concept_ready",
  "generated_at": "2025-08-08T19:00:00"
}
```

### Text Content
```json
{
  "id": "txt_1",
  "title": "Social Media Post", 
  "content": "Engaging social media content...",
  "platform": "instagram",
  "generated_at": "2025-08-08T19:00:00"
}
```

## Campaign Storage

Each campaign is saved as an individual JSON file in the `campaign_storage/` directory:

```
campaign_storage/
├── abc123-uuid-456.json
├── def789-uuid-012.json
└── ...
```

Campaign files contain:
- Original URL and scraped website data
- Competitor analysis results  
- Complete marketing strategy
- All generated content prompts
- Final generated content (images, videos, text)
- Timestamps and metadata

## Error Handling

- **API Failures**: Graceful fallbacks and error reporting
- **Invalid URLs**: Input validation and user feedback  
- **Missing Keys**: Clear error messages for missing API configurations
- **Rate Limits**: Proper error handling for API rate limits
- **Network Issues**: Timeout handling and retry logic

## Customization

### Adding New Content Types
1. Extend `_generate_content_prompts()` with new prompt categories
2. Add corresponding generation method in `_generate_ai_content()`
3. Update the frontend display components

### Custom API Integrations
1. Add new API client initialization in `__init__()`
2. Create generation methods following the existing pattern
3. Update the content generation orchestrator

## Testing

Run the test suite to validate functionality:

```bash
python test_campaign_generator.py
```

The test suite validates:
- Website scraping functionality
- Competitor analysis
- API connectivity
- Complete workflow execution
- Generated content structure

## Production Considerations

- **API Rate Limits**: Implement proper rate limiting and queuing
- **Caching**: Add Redis caching for repeated website analyses
- **Database**: Consider migrating from JSON files to proper database
- **Authentication**: Add user authentication and campaign ownership
- **Monitoring**: Add comprehensive logging and monitoring
- **Scaling**: Consider async processing queues for high-volume usage

## Troubleshooting

### Common Issues

1. **"No module named reflex"**
   - Install Reflex: `pip install reflex`

2. **"API key not configured"**
   - Check .env file exists and has correct API keys
   - Verify API key format and permissions

3. **"Website scraping failed"**
   - Check URL accessibility
   - Verify trafilatura installation
   - Some sites may block automated scraping

4. **"Image generation failed"**
   - Verify OpenAI API key has DALL-E access
   - Check API usage limits and billing

## Future Enhancements

- **Google Veo3 Integration**: Replace placeholder with actual video generation
- **Advanced Competitor Analysis**: Use AI to analyze competitor content
- **Content Scheduling**: Add social media scheduling capabilities
- **A/B Testing**: Generate multiple content variations
- **Analytics Dashboard**: Track campaign performance metrics
- **Template System**: Customizable campaign templates by industry