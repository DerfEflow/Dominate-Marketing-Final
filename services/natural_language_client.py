"""
Google Natural Language API Client - Aspect-based sentiment analysis
Analyzes review sentiment and extracts business-relevant aspects
"""

import os
import logging
from typing import Dict, List, Any, Optional
# google-cloud-language is an OPTIONAL dependency (not in requirements.txt).
# Guard the import so this module — and anything that imports it — still loads
# when the package is absent. The client stays None and features no-op.
try:
    from google.cloud import language_v1
    LANGUAGE_API_AVAILABLE = True
except ImportError:
    language_v1 = None
    LANGUAGE_API_AVAILABLE = False

class NaturalLanguageClient:
    """
    Google Natural Language API client for sentiment and entity analysis
    Provides aspect-based sentiment analysis for competitor reviews
    """
    
    def __init__(self):
        # Service account credentials via environment variable
        self.credentials_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
        
        if self.credentials_path and LANGUAGE_API_AVAILABLE:
            self.client = language_v1.LanguageServiceClient()
        else:
            if not LANGUAGE_API_AVAILABLE:
                logging.warning("google-cloud-language not installed — Natural Language features disabled")
            else:
                logging.warning("Google Natural Language API credentials not found")
            self.client = None
    
    def validate_credentials(self) -> bool:
        """Check if Natural Language API credentials are available"""
        return self.client is not None
    
    async def analyze_review_sentiment(self, review_text: str) -> Dict[str, Any]:
        """
        Analyze sentiment of a single review with entity extraction
        """
        if not self.validate_credentials():
            raise ValueError("Google Natural Language API credentials required")
        
        try:
            document = language_v1.Document(
                content=review_text,
                type_=language_v1.Document.Type.PLAIN_TEXT
            )
            
            # Analyze sentiment
            sentiment_response = self.client.analyze_sentiment(
                request={"document": document}
            )
            
            # Extract entities and their sentiment
            entity_response = self.client.analyze_entity_sentiment(
                request={"document": document}
            )
            
            # Process results
            overall_sentiment = sentiment_response.document_sentiment
            entities = []
            
            for entity in entity_response.entities:
                entities.append({
                    'name': entity.name,
                    'type': entity.type_.name,
                    'salience': entity.salience,
                    'sentiment_score': entity.sentiment.score,
                    'sentiment_magnitude': entity.sentiment.magnitude,
                    'mentions': [mention.text.content for mention in entity.mentions]
                })
            
            return {
                'overall_sentiment': {
                    'score': overall_sentiment.score,
                    'magnitude': overall_sentiment.magnitude
                },
                'entities': entities,
                'text_length': len(review_text),
                'analysis_method': 'google_natural_language_api'
            }
            
        except Exception as e:
            logging.error(f"Natural Language API error: {e}")
            raise
    
    async def analyze_aspect_sentiment(self, reviews: List[str], business_aspects: List[str]) -> Dict[str, Any]:
        """
        Analyze sentiment for specific business aspects across multiple reviews
        """
        if not self.validate_credentials():
            raise ValueError("Google Natural Language API credentials required")
        
        try:
            aspect_sentiments = {aspect: {'positive': 0, 'negative': 0, 'neutral': 0, 'mentions': []} for aspect in business_aspects}
            overall_stats = {'total_reviews': len(reviews), 'processed': 0, 'errors': 0}
            
            for review in reviews:
                try:
                    analysis = await self.analyze_review_sentiment(review)
                    overall_stats['processed'] += 1
                    
                    # Check each entity against business aspects
                    for entity in analysis['entities']:
                        entity_name = entity['name'].lower()
                        
                        for aspect in business_aspects:
                            if aspect.lower() in entity_name or any(mention.lower() in review.lower() for mention in entity['mentions']):
                                sentiment_score = entity['sentiment_score']
                                
                                if sentiment_score > 0.1:
                                    aspect_sentiments[aspect]['positive'] += 1
                                elif sentiment_score < -0.1:
                                    aspect_sentiments[aspect]['negative'] += 1
                                else:
                                    aspect_sentiments[aspect]['neutral'] += 1
                                
                                aspect_sentiments[aspect]['mentions'].append({
                                    'text': entity['name'],
                                    'sentiment': sentiment_score,
                                    'review_snippet': review[:100] + '...'
                                })
                
                except Exception as e:
                    logging.warning(f"Review analysis failed: {e}")
                    overall_stats['errors'] += 1
            
            # Calculate aspect scores
            for aspect in aspect_sentiments:
                total = sum(aspect_sentiments[aspect][key] for key in ['positive', 'negative', 'neutral'])
                if total > 0:
                    aspect_sentiments[aspect]['score'] = (
                        aspect_sentiments[aspect]['positive'] - aspect_sentiments[aspect]['negative']
                    ) / total
                else:
                    aspect_sentiments[aspect]['score'] = 0
            
            return {
                'aspect_sentiments': aspect_sentiments,
                'overall_stats': overall_stats,
                'analysis_method': 'google_natural_language_api'
            }
            
        except Exception as e:
            logging.error(f"Aspect sentiment analysis error: {e}")
            raise
    
    async def extract_business_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract business-relevant entities from text
        """
        if not self.validate_credentials():
            raise ValueError("Google Natural Language API credentials required")
        
        try:
            document = language_v1.Document(
                content=text,
                type_=language_v1.Document.Type.PLAIN_TEXT
            )
            
            response = self.client.analyze_entities(
                request={"document": document}
            )
            
            entities = []
            for entity in response.entities:
                entities.append({
                    'name': entity.name,
                    'type': entity.type_.name,
                    'salience': entity.salience,
                    'mentions': [mention.text.content for mention in entity.mentions],
                    'metadata': dict(entity.metadata)
                })
            
            return entities
            
        except Exception as e:
            logging.error(f"Entity extraction error: {e}")
            raise
    
    def get_required_credentials_info(self) -> Dict[str, str]:
        """
        Return information about required Natural Language API credentials
        """
        return {
            'GOOGLE_APPLICATION_CREDENTIALS': 'Path to service account JSON file',
            'setup_instructions': 'https://cloud.google.com/natural-language/docs/setup',
            'required_apis': ['Natural Language API'],
            'service_account_roles': [
                'Cloud Natural Language API User'
            ]
        }