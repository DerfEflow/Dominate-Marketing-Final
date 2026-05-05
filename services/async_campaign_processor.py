"""
Asynchronous campaign processing system to handle heavy AI workloads
without blocking the web interface or crashing workers.
"""

import logging
import json
import time
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from threading import Thread
import queue
import sqlite3
import os

logger = logging.getLogger(__name__)

class AsyncCampaignProcessor:
    """Handles campaign generation in background threads to prevent worker crashes"""
    
    def __init__(self):
        self.job_queue = queue.Queue()
        self.results_db = "campaign_results.db"
        self.init_results_database()
        self.start_worker_thread()
    
    def init_results_database(self):
        """Initialize SQLite database for storing campaign results"""
        conn = sqlite3.connect(self.results_db)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS campaign_jobs (
                job_id TEXT PRIMARY KEY,
                user_id TEXT,
                status TEXT,
                business_url TEXT,
                created_at TIMESTAMP,
                completed_at TIMESTAMP,
                result_data TEXT,
                error_message TEXT
            )
        ''')
        conn.commit()
        conn.close()
    
    def start_worker_thread(self):
        """Start background worker thread for processing campaigns"""
        worker_thread = Thread(target=self._process_campaigns_worker, daemon=True)
        worker_thread.start()
        logger.info("Campaign processor worker thread started")
    
    def submit_job(self, business_url: str, target_audience: str, campaign_goal: str, user_id: str = None, campaign_params: Dict = None) -> str:
        """Submit a campaign generation job and return job ID immediately"""
        if campaign_params is None:
            campaign_params = {'target_audience': target_audience, 'campaign_goal': campaign_goal}
        job_id = str(uuid.uuid4())
        
        # Store initial job record
        conn = sqlite3.connect(self.results_db)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO campaign_jobs (job_id, user_id, status, business_url, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (job_id, user_id, 'queued', business_url, datetime.now().isoformat()))
        conn.commit()
        conn.close()
        
        # Add to processing queue
        job_data = {
            'job_id': job_id,
            'user_id': user_id,
            'business_url': business_url,
            'campaign_params': campaign_params,
            'submitted_at': datetime.now().isoformat()
        }
        self.job_queue.put(job_data)
        
        logger.info(f"Campaign job {job_id} submitted for user {user_id}")
        return job_id
    
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get current status and results for a job"""
        conn = sqlite3.connect(self.results_db)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT status, result_data, error_message, created_at, completed_at
            FROM campaign_jobs WHERE job_id = ?
        ''', (job_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return {'status': 'not_found'}
        
        status, result_data, error_message, created_at, completed_at = row
        
        result = {
            'status': status,
            'created_at': created_at,
            'completed_at': completed_at
        }
        
        if result_data:
            result['data'] = json.loads(result_data)
        
        if error_message:
            result['error'] = error_message
        
        return result
    
    def _process_campaigns_worker(self):
        """Background worker that processes campaign generation jobs"""
        logger.info("Campaign processor worker started")
        
        while True:
            try:
                # Wait for next job
                job_data = self.job_queue.get(timeout=1)
                logger.info(f"Processing campaign job {job_data['job_id']}")
                
                # Update status to processing
                self._update_job_status(job_data['job_id'], 'processing')
                
                # Process the campaign
                try:
                    result = self._generate_campaign_safely(job_data)
                    
                    # Store successful result
                    self._update_job_status(
                        job_data['job_id'], 
                        'completed',
                        result_data=json.dumps(result)
                    )
                    
                except Exception as e:
                    logger.error(f"Error processing job {job_data['job_id']}: {e}")
                    
                    # Store error result
                    self._update_job_status(
                        job_data['job_id'], 
                        'failed',
                        error_message=str(e)
                    )
                
                # Mark job as done
                self.job_queue.task_done()
                
            except queue.Empty:
                # No jobs in queue, continue waiting
                continue
            except Exception as e:
                logger.error(f"Worker thread error: {e}")
                time.sleep(1)
    
    def _update_job_status(self, job_id: str, status: str, result_data: str = None, error_message: str = None):
        """Update job status in database"""
        conn = sqlite3.connect(self.results_db)
        cursor = conn.cursor()
        
        completed_at = datetime.now().isoformat() if status in ['completed', 'failed'] else None
        
        cursor.execute('''
            UPDATE campaign_jobs 
            SET status = ?, completed_at = ?, result_data = ?, error_message = ?
            WHERE job_id = ?
        ''', (status, completed_at, result_data, error_message, job_id))
        
        conn.commit()
        conn.close()
    
    def _generate_campaign_safely(self, job_data: Dict) -> Dict[str, Any]:
        """Generate campaign with proper error handling and resource management"""
        try:
            # Import services only when needed to avoid blocking startup
            from services.sell_profile_analyzer import SellProfileAnalyzer
            from services.viral_tools_researcher import ViralToolsResearcher
            from services.content_generator import ContentGenerator
            from services.quality_agent import QualityAgent
            
            business_url = job_data['business_url']
            campaign_params = job_data['campaign_params']
            
            # Step 1: Analyze website (with timeout)
            logger.info(f"Analyzing website: {business_url}")
            profile_analyzer = SellProfileAnalyzer()
            sell_profile = profile_analyzer.analyze_website(business_url)
            profile_data = profile_analyzer.export_profile(sell_profile)
            
            # Step 2: Research viral tools (with reduced intensity)
            logger.info("Researching viral tools")
            viral_researcher = ViralToolsResearcher()
            viral_tools = viral_researcher.research_viral_tools(profile_data)
            viral_data = viral_researcher.export_research(viral_tools)
            
            # Step 3: Generate content (with rate limiting)
            logger.info("Generating content")
            content_generator = ContentGenerator()
            user_tier = campaign_params.get('tier', 'basic')
            generated_content = content_generator.generate_campaign_content(
                profile_data, viral_data, tier=user_tier
            )
            
            # Step 4: Quality validation
            logger.info("Validating quality")
            quality_agent = QualityAgent()
            quality_validation = quality_agent.validate_campaign_content(
                generated_content, profile_data
            )
            
            # Compile final result
            result = {
                'success': True,
                'sell_profile': profile_data,
                'viral_tools': viral_data,
                'generated_content': generated_content,
                'quality_validation': quality_validation,
                'campaign_params': campaign_params,
                'processed_at': datetime.now().isoformat()
            }
            
            logger.info(f"Campaign generation completed successfully for job {job_data['job_id']}")
            return result
            
        except Exception as e:
            logger.error(f"Campaign generation failed: {e}")
            raise e

# Global processor instance
campaign_processor = AsyncCampaignProcessor()