import os
import json
import uuid
import logging
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_required, current_user
from datetime import datetime
from dotenv import load_dotenv
from models import db, User
from auth import auth
from dashboard import dashboard

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")

# Ensure outputs directory exists
os.makedirs('outputs', exist_ok=True)

@app.route('/')
def index():
    """Homepage with the campaign data collection form"""
    return render_template('index.html')

# FAQ route moved to main_app.py to avoid conflicts

@app.route('/generate', methods=['POST'])
def generate():
    """Handle form submission, validate data, save to JSON, and redirect to results"""
    try:
        # Extract form data
        business_url = request.form.get('business_url', '').strip()
        brand_voice = request.form.get('brand_voice', '')
        goal = request.form.get('goal', '')
        region = request.form.get('region', '').strip()
        platform = request.form.get('platform', '')
        video_length = request.form.get('video_length', '')
        cta_text = request.form.get('cta_text', '').strip()
        logo_url = request.form.get('logo_url', '').strip()
        
        # Validate required fields
        if not business_url:
            flash('Business URL is required', 'error')
            return redirect(url_for('index'))
        
        # Generate unique job ID
        job_id = str(uuid.uuid4())
        
        # Prepare data structure
        campaign_data = {
            'job_id': job_id,
            'timestamp': datetime.now().isoformat(),
            'business_url': business_url,
            'brand_voice': brand_voice,
            'goal': goal,
            'region': region,
            'platform': platform,
            'video_length': int(video_length) if video_length else None,
            'cta_text': cta_text,
            'logo_url': logo_url if logo_url else None
        }
        
        # Create job directory using pathlib
        job_dir = Path('outputs') / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        
        # Save campaign data to JSON file
        (job_dir / 'campaign.json').write_text(json.dumps(campaign_data, indent=2))
        app.logger.info(f"Campaign data saved for job ID: {job_id}")
        
        # Generate business summary using OpenAI
        app.logger.info(f"Generating business summary for URL: {business_url}")
        summary_result = summarize_url(business_url, brand_voice or 'neutral')
        (job_dir / 'summary.json').write_text(json.dumps(summary_result, indent=2))
        app.logger.info(f"Business summary saved for job ID: {job_id}")
        
        # Generate ad script using OpenAI
        app.logger.info(f"Generating ad script for job ID: {job_id}")
        script_json = build_ad_script(
            business_url=business_url,
            region=region or 'Global',
            goal=goal or 'awareness',
            brand_voice=brand_voice or 'friendly',
            cta=cta_text or 'Learn More',
            length_sec=int(video_length) if video_length else 30
        )
        (job_dir / 'script.json').write_text(json.dumps(script_json, indent=2))
        app.logger.info(f"Ad script saved for job ID: {job_id}")
        
        # Build Veo 3 request
        app.logger.info(f"Building Veo 3 request for job ID: {job_id}")
        veo_request = build_veo3_request(
            script_json=script_json,
            brand_voice=brand_voice or 'friendly',
            cta=cta_text or 'Learn More',
            length_sec=int(video_length) if video_length else 30,
            logo_url=logo_url
        )
        (job_dir / 'veo_request.json').write_text(json.dumps(veo_request, indent=2))
        app.logger.info(f"Veo 3 request saved for job ID: {job_id}")
        
        # Generate actual video with Veo 3
        app.logger.info(f"Starting Veo 3 video generation for job ID: {job_id}")
        video_prompt = build_veo3_prompt_from_script(
            script_json=script_json,
            brand_voice=brand_voice or 'friendly',
            cta=cta_text or 'Learn More'
        )
        
        video_result = generate_video_with_veo3(
            prompt=video_prompt,
            length_seconds=int(video_length) if video_length else 30,
            aspect_ratio="9:16"
        )
        
        # Save video generation result
        (job_dir / 'video_result.json').write_text(json.dumps(video_result, indent=2))
        app.logger.info(f"Video generation result saved for job ID: {job_id}")
        
        # Redirect to results page (Post-Redirect-Get pattern)
        return redirect(url_for('result', job_id=job_id))
        
    except Exception as e:
        app.logger.error(f"Error processing form submission: {str(e)}")
        flash('An error occurred while processing your submission. Please try again.', 'error')
        return redirect(url_for('index'))

@app.route('/result/<job_id>')
def result(job_id):
    """Display the results page for a specific job ID"""
    try:
        # Load campaign data from JSON file
        job_dir = os.path.join('outputs', job_id)
        campaign_file = os.path.join(job_dir, 'campaign.json')
        summary_file = os.path.join(job_dir, 'summary.json')
        script_file = os.path.join(job_dir, 'script.json')
        veo_file = os.path.join(job_dir, 'veo_request.json')
        video_file = os.path.join(job_dir, 'video_result.json')
        
        if not os.path.exists(campaign_file):
            flash('Campaign data not found', 'error')
            return redirect(url_for('index'))
        
        with open(campaign_file, 'r') as f:
            campaign_data = json.load(f)
        
        # Load summary data if available
        summary_data = None
        if os.path.exists(summary_file):
            with open(summary_file, 'r') as f:
                summary_data = json.load(f)
        
        # Load script data if available
        script_data = None
        if os.path.exists(script_file):
            with open(script_file, 'r') as f:
                script_data = json.load(f)
        
        # Load veo request data if available
        veo_data = None
        if os.path.exists(veo_file):
            with open(veo_file, 'r') as f:
                veo_data = json.load(f)
        
        # Load video generation result if available
        video_data = None
        if os.path.exists(video_file):
            with open(video_file, 'r') as f:
                video_data = json.load(f)
        
        return render_template('result.html', 
                             data=campaign_data, 
                             summary=summary_data,
                             script=script_data,
                             veo_request=veo_data,
                             video_result=video_data)
        
    except Exception as e:
        app.logger.error(f"Error loading results for job ID {job_id}: {str(e)}")
        flash('An error occurred while loading the results. Please try again.', 'error')
        return redirect(url_for('index'))

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return render_template('index.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    app.logger.error(f"Internal server error: {str(error)}")
    flash('An internal error occurred. Please try again.', 'error')
    return render_template('index.html'), 500
