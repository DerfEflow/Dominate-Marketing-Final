"""
Strategy Data Repository - Storage and retrieval system for marketing analysis data
Associates comprehensive analysis data with specific campaigns within user brands
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy import and_, desc, func
from flask import current_app

from models import db, Campaign, Brand, User, StrategyAnalysis

class StrategyDataRepository:
    """
    Repository for storing, retrieving, and managing marketing strategy analysis data
    Provides structured access to comprehensive website analysis and market intelligence
    """
    
    def __init__(self):
        self.confidence_threshold = 0.6  # Minimum confidence score for reliable data
        
    def store_analysis(self, analysis_data: Dict[str, Any], brand_id: str, campaign_id: str = None) -> str:
        """
        Store comprehensive analysis data with proper indexing and relationships
        """
        try:
            # Create new campaign if not provided
            if not campaign_id:
                campaign = Campaign(
                    brand_id=brand_id,
                    campaign_type='strategy_analysis',
                    status='completed',
                    target_url=analysis_data.get('url', ''),
                    created_at=datetime.utcnow()
                )
                db.session.add(campaign)
                db.session.flush()  # Get the ID
                campaign_id = campaign.id
            
            # Create detailed analysis record
            strategy_analysis = StrategyAnalysis(
                campaign_id=campaign_id,
                brand_id=brand_id,
                target_url=analysis_data.get('url', ''),
                geo_location=analysis_data.get('geo_location', 'US'),
                confidence_score=analysis_data.get('confidence_score', 0.0),
                data_sources=json.dumps(analysis_data.get('data_sources', [])),
                
                # Business Intelligence Data
                business_intelligence=json.dumps(analysis_data.get('business_intelligence', {})),
                competitor_analysis=json.dumps(analysis_data.get('competitor_analysis', {})),
                trend_analysis=json.dumps(analysis_data.get('trend_analysis', {})),
                content_opportunities=json.dumps(analysis_data.get('content_opportunities', {})),
                
                # Technical Analysis Data
                scraping_successful=not analysis_data.get('fallback_used', False),
                fallback_protocols_used=analysis_data.get('fallback_used', False),
                metadata_extracted=bool(analysis_data.get('business_intelligence', {}).get('technical_info')),
                
                # Analysis Timestamp
                analysis_timestamp=datetime.fromisoformat(analysis_data['timestamp'].replace('Z', '+00:00')),
                created_at=datetime.utcnow()
            )
            
            db.session.add(strategy_analysis)
            db.session.commit()
            
            logging.info(f"Strategy analysis stored successfully for campaign {campaign_id}")
            return str(strategy_analysis.id)
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Failed to store analysis data: {e}")
            raise
    
    def get_analysis_by_campaign(self, campaign_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve complete analysis data for a specific campaign
        """
        try:
            analysis = StrategyAnalysis.query.filter_by(campaign_id=campaign_id).first()
            
            if not analysis:
                return None
            
            return self._serialize_analysis(analysis)
            
        except Exception as e:
            logging.error(f"Failed to retrieve analysis for campaign {campaign_id}: {e}")
            return None
    
    def get_latest_analysis_by_brand(self, brand_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the most recent analysis for a brand
        """
        try:
            analysis = StrategyAnalysis.query.filter_by(brand_id=brand_id)\
                .order_by(desc(StrategyAnalysis.created_at))\
                .first()
            
            if not analysis:
                return None
            
            return self._serialize_analysis(analysis)
            
        except Exception as e:
            logging.error(f"Failed to retrieve latest analysis for brand {brand_id}: {e}")
            return None
    
    def get_analysis_by_url(self, url: str, brand_id: str = None) -> List[Dict[str, Any]]:
        """
        Get all analyses for a specific URL, optionally filtered by brand
        """
        try:
            query = StrategyAnalysis.query.filter_by(target_url=url)
            
            if brand_id:
                query = query.filter_by(brand_id=brand_id)
            
            analyses = query.order_by(desc(StrategyAnalysis.created_at)).all()
            
            return [self._serialize_analysis(analysis) for analysis in analyses]
            
        except Exception as e:
            logging.error(f"Failed to retrieve analyses for URL {url}: {e}")
            return []
    
    def get_high_confidence_analyses(self, brand_id: str, min_confidence: float = None) -> List[Dict[str, Any]]:
        """
        Get high-confidence analyses for strategic decision making
        """
        try:
            min_conf = min_confidence or self.confidence_threshold
            
            analyses = StrategyAnalysis.query.filter(
                and_(
                    StrategyAnalysis.brand_id == brand_id,
                    StrategyAnalysis.confidence_score >= min_conf
                )
            ).order_by(desc(StrategyAnalysis.confidence_score)).all()
            
            return [self._serialize_analysis(analysis) for analysis in analyses]
            
        except Exception as e:
            logging.error(f"Failed to retrieve high-confidence analyses: {e}")
            return []
    
    def get_trend_summary(self, brand_id: str, days_back: int = 30) -> Dict[str, Any]:
        """
        Generate trend summary from recent analyses
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)
            
            analyses = StrategyAnalysis.query.filter(
                and_(
                    StrategyAnalysis.brand_id == brand_id,
                    StrategyAnalysis.created_at >= cutoff_date
                )
            ).all()
            
            if not analyses:
                return {'message': 'No recent analyses found'}
            
            # Aggregate trend data
            all_trends = []
            all_competitors = []
            content_opportunities = []
            
            for analysis in analyses:
                # Parse trend data
                trend_data = json.loads(analysis.trend_analysis or '{}')
                if trend_data.get('rising_topics'):
                    all_trends.extend(trend_data['rising_topics'])
                
                # Parse competitor data
                competitor_data = json.loads(analysis.competitor_analysis or '{}')
                if competitor_data.get('direct_competitors'):
                    all_competitors.extend(competitor_data['direct_competitors'])
                
                # Parse content opportunities
                content_data = json.loads(analysis.content_opportunities or '{}')
                if content_data.get('trending_topics'):
                    content_opportunities.extend(content_data['trending_topics'])
            
            return {
                'period': f'{days_back} days',
                'total_analyses': len(analyses),
                'trending_topics': list(set(all_trends))[:10],  # Top 10 unique trends
                'competitor_insights': self._aggregate_competitors(all_competitors),
                'content_opportunities': list(set(content_opportunities))[:15],
                'average_confidence': sum(a.confidence_score for a in analyses) / len(analyses)
            }
            
        except Exception as e:
            logging.error(f"Failed to generate trend summary: {e}")
            return {'error': str(e)}
    
    def get_competitive_intelligence(self, brand_id: str) -> Dict[str, Any]:
        """
        Compile competitive intelligence from all analyses
        """
        try:
            analyses = StrategyAnalysis.query.filter_by(brand_id=brand_id)\
                .filter(StrategyAnalysis.confidence_score >= self.confidence_threshold)\
                .all()
            
            if not analyses:
                return {'message': 'No high-confidence competitive data available'}
            
            # Aggregate competitive data
            all_competitors = {}
            market_gaps = set()
            pricing_insights = {}
            
            for analysis in analyses:
                competitor_data = json.loads(analysis.competitor_analysis or '{}')
                
                # Aggregate competitor information
                if competitor_data.get('direct_competitors'):
                    for comp in competitor_data['direct_competitors']:
                        comp_name = comp.get('name', 'Unknown')
                        if comp_name not in all_competitors:
                            all_competitors[comp_name] = {
                                'mentions': 0,
                                'strengths': [],
                                'weaknesses': [],
                                'avg_strength': 0
                            }
                        
                        all_competitors[comp_name]['mentions'] += 1
                        if comp.get('strength'):
                            all_competitors[comp_name]['avg_strength'] = (
                                all_competitors[comp_name]['avg_strength'] + comp['strength']
                            ) / all_competitors[comp_name]['mentions']
                        
                        if comp.get('weakness'):
                            all_competitors[comp_name]['weaknesses'].append(comp['weakness'])
                
                # Aggregate market gaps
                if competitor_data.get('market_gaps'):
                    market_gaps.update(competitor_data['market_gaps'])
                
                # Aggregate pricing insights
                if competitor_data.get('pricing_insights'):
                    pricing_insights.update(competitor_data['pricing_insights'])
            
            return {
                'competitors': all_competitors,
                'market_opportunities': list(market_gaps),
                'pricing_intelligence': pricing_insights,
                'analysis_count': len(analyses)
            }
            
        except Exception as e:
            logging.error(f"Failed to compile competitive intelligence: {e}")
            return {'error': str(e)}
    
    def get_content_strategy_data(self, brand_id: str) -> Dict[str, Any]:
        """
        Compile content strategy recommendations from analyses
        """
        try:
            latest_analysis = self.get_latest_analysis_by_brand(brand_id)
            
            if not latest_analysis:
                return {'message': 'No analysis data available for content strategy'}
            
            content_data = latest_analysis.get('content_opportunities', {})
            
            # Structure content strategy data
            strategy_data = {
                'trending_topics': content_data.get('trending_topics', []),
                'seasonal_content': content_data.get('seasonal_content', []),
                'local_opportunities': content_data.get('local_opportunities', []),
                'content_calendar': content_data.get('content_calendar', [])[:7],  # Next 7 days
                'hook_suggestions': content_data.get('hook_suggestions', []),
                'cta_variations': content_data.get('cta_variations', []),
                'competitor_gaps': content_data.get('competitor_gaps', []),
                'confidence_score': latest_analysis.get('confidence_score', 0.0),
                'last_updated': latest_analysis.get('analysis_timestamp')
            }
            
            return strategy_data
            
        except Exception as e:
            logging.error(f"Failed to compile content strategy data: {e}")
            return {'error': str(e)}
    
    def update_analysis_confidence(self, analysis_id: str, new_confidence: float, notes: str = None):
        """
        Update confidence score based on performance or manual review
        """
        try:
            analysis = StrategyAnalysis.query.get(analysis_id)
            
            if not analysis:
                raise ValueError(f"Analysis {analysis_id} not found")
            
            old_confidence = analysis.confidence_score
            analysis.confidence_score = new_confidence
            
            if notes:
                # Store confidence update history
                update_record = {
                    'timestamp': datetime.utcnow().isoformat(),
                    'old_confidence': old_confidence,
                    'new_confidence': new_confidence,
                    'notes': notes
                }
                
                # Add to existing update history or create new
                existing_updates = json.loads(analysis.update_history or '[]')
                existing_updates.append(update_record)
                analysis.update_history = json.dumps(existing_updates)
            
            db.session.commit()
            logging.info(f"Updated confidence for analysis {analysis_id}: {old_confidence} -> {new_confidence}")
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Failed to update analysis confidence: {e}")
            raise
    
    def delete_analysis(self, analysis_id: str):
        """
        Delete analysis data (with proper cleanup)
        """
        try:
            analysis = StrategyAnalysis.query.get(analysis_id)
            
            if not analysis:
                raise ValueError(f"Analysis {analysis_id} not found")
            
            db.session.delete(analysis)
            db.session.commit()
            
            logging.info(f"Deleted analysis {analysis_id}")
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Failed to delete analysis: {e}")
            raise
    
    def cleanup_old_analyses(self, days_to_keep: int = 90):
        """
        Clean up old analyses to manage storage
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            
            old_analyses = StrategyAnalysis.query.filter(
                StrategyAnalysis.created_at < cutoff_date
            ).all()
            
            count = len(old_analyses)
            
            for analysis in old_analyses:
                db.session.delete(analysis)
            
            db.session.commit()
            
            logging.info(f"Cleaned up {count} old analyses (older than {days_to_keep} days)")
            return count
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Failed to cleanup old analyses: {e}")
            return 0
    
    def _serialize_analysis(self, analysis: StrategyAnalysis) -> Dict[str, Any]:
        """
        Convert database analysis record to dictionary format
        """
        return {
            'id': analysis.id,
            'campaign_id': analysis.campaign_id,
            'brand_id': analysis.brand_id,
            'target_url': analysis.target_url,
            'geo_location': analysis.geo_location,
            'confidence_score': analysis.confidence_score,
            'data_sources': json.loads(analysis.data_sources or '[]'),
            'business_intelligence': json.loads(analysis.business_intelligence or '{}'),
            'competitor_analysis': json.loads(analysis.competitor_analysis or '{}'),
            'trend_analysis': json.loads(analysis.trend_analysis or '{}'),
            'content_opportunities': json.loads(analysis.content_opportunities or '{}'),
            'scraping_successful': analysis.scraping_successful,
            'fallback_protocols_used': analysis.fallback_protocols_used,
            'metadata_extracted': analysis.metadata_extracted,
            'analysis_timestamp': analysis.analysis_timestamp.isoformat(),
            'created_at': analysis.created_at.isoformat(),
            'update_history': json.loads(analysis.update_history or '[]')
        }
    
    def _aggregate_competitors(self, competitors: List[Dict]) -> Dict[str, Any]:
        """
        Aggregate competitor data from multiple analyses
        """
        aggregated = {}
        
        for comp in competitors:
            name = comp.get('name', 'Unknown')
            if name not in aggregated:
                aggregated[name] = {
                    'mentions': 0,
                    'avg_strength': 0,
                    'common_weaknesses': []
                }
            
            aggregated[name]['mentions'] += 1
            if comp.get('strength'):
                current_avg = aggregated[name]['avg_strength']
                mentions = aggregated[name]['mentions']
                aggregated[name]['avg_strength'] = (current_avg * (mentions - 1) + comp['strength']) / mentions
            
            if comp.get('weakness'):
                aggregated[name]['common_weaknesses'].append(comp['weakness'])
        
        return aggregated