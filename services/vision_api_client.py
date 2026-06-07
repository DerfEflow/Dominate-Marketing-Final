"""
Google Vision API Client - Aesthetic analysis and OCR
Analyzes competitor thumbnails and visual content for style patterns
"""

import os
import logging
import base64
from typing import Dict, List, Any, Optional
# google-cloud-vision is an OPTIONAL dependency (not in requirements.txt).
# Guard the import so this module — and anything that imports it — still loads
# when the package is absent. The client stays None and features no-op.
try:
    from google.cloud import vision
    VISION_API_AVAILABLE = True
except ImportError:
    vision = None
    VISION_API_AVAILABLE = False

class VisionAPIClient:
    """
    Google Vision API client for visual content analysis
    Provides aesthetic analysis and OCR capabilities for competitor intelligence
    """
    
    def __init__(self):
        # Service account credentials via environment variable
        self.credentials_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
        
        if self.credentials_path and VISION_API_AVAILABLE:
            self.client = vision.ImageAnnotatorClient()
        else:
            if not VISION_API_AVAILABLE:
                logging.warning("google-cloud-vision not installed — Vision features disabled")
            else:
                logging.warning("Google Vision API credentials not found")
            self.client = None
    
    def validate_credentials(self) -> bool:
        """Check if Vision API credentials are available"""
        return self.client is not None
    
    async def analyze_image_aesthetics(self, image_url: str) -> Dict[str, Any]:
        """
        Analyze image aesthetics including composition, colors, and visual elements
        """
        if not self.validate_credentials():
            raise ValueError("Google Vision API credentials required")
        
        try:
            # Download and analyze image
            import requests
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()
            
            image_content = response.content
            image = vision.Image(content=image_content)
            
            # Multiple detection types
            features = [
                vision.Feature(type_=vision.Feature.Type.LABEL_DETECTION, max_results=20),
                vision.Feature(type_=vision.Feature.Type.IMAGE_PROPERTIES),
                vision.Feature(type_=vision.Feature.Type.SAFE_SEARCH_DETECTION),
                vision.Feature(type_=vision.Feature.Type.OBJECT_LOCALIZATION, max_results=10),
                vision.Feature(type_=vision.Feature.Type.TEXT_DETECTION)
            ]
            
            request = vision.AnnotateImageRequest(image=image, features=features)
            response = self.client.annotate_image(request=request)
            
            if response.error.message:
                raise Exception(f"Vision API error: {response.error.message}")
            
            # Process results
            analysis = {
                'labels': [],
                'dominant_colors': [],
                'objects': [],
                'text_content': [],
                'aesthetic_score': 0,
                'style_classification': '',
                'composition_analysis': {},
                'source_url': image_url
            }
            
            # Process labels
            for label in response.label_annotations:
                analysis['labels'].append({
                    'description': label.description,
                    'score': label.score,
                    'topicality': label.topicality
                })
            
            # Process color properties
            if response.image_properties_annotation:
                colors = response.image_properties_annotation.dominant_colors
                for color in colors.colors:
                    rgb = color.color
                    analysis['dominant_colors'].append({
                        'red': rgb.red,
                        'green': rgb.green,
                        'blue': rgb.blue,
                        'pixel_fraction': color.pixel_fraction,
                        'score': color.score
                    })
            
            # Process objects
            for obj in response.localized_object_annotations:
                vertices = []
                for vertex in obj.bounding_poly.normalized_vertices:
                    vertices.append({'x': vertex.x, 'y': vertex.y})
                
                analysis['objects'].append({
                    'name': obj.name,
                    'score': obj.score,
                    'bounding_poly': vertices
                })
            
            # Process text
            if response.text_annotations:
                for text in response.text_annotations:
                    analysis['text_content'].append({
                        'text': text.description,
                        'confidence': getattr(text, 'confidence', 0)
                    })
            
            # Calculate aesthetic and composition metrics
            analysis['aesthetic_score'] = self._calculate_aesthetic_score(analysis)
            analysis['style_classification'] = self._classify_visual_style(analysis)
            analysis['composition_analysis'] = self._analyze_composition(analysis)
            
            return analysis
            
        except Exception as e:
            logging.error(f"Vision API error: {e}")
            raise
    
    async def extract_text_from_image(self, image_url: str) -> Dict[str, Any]:
        """
        Extract text content from images using OCR
        """
        if not self.validate_credentials():
            raise ValueError("Google Vision API credentials required")
        
        try:
            import requests
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()
            
            image = vision.Image(content=response.content)
            
            # Text detection
            response = self.client.text_detection(image=image)
            texts = response.text_annotations
            
            if response.error.message:
                raise Exception(f"Vision API error: {response.error.message}")
            
            extracted_text = {
                'full_text': '',
                'text_blocks': [],
                'confidence_score': 0,
                'source_url': image_url
            }
            
            if texts:
                extracted_text['full_text'] = texts[0].description
                
                for text in texts[1:]:  # Skip first (full text)
                    vertices = []
                    for vertex in text.bounding_poly.vertices:
                        vertices.append({'x': vertex.x, 'y': vertex.y})
                    
                    extracted_text['text_blocks'].append({
                        'text': text.description,
                        'bounding_poly': vertices
                    })
            
            return extracted_text
            
        except Exception as e:
            logging.error(f"Text extraction error: {e}")
            raise
    
    async def analyze_competitor_thumbnails(self, thumbnail_urls: List[str]) -> Dict[str, Any]:
        """
        Analyze multiple competitor thumbnails to identify winning patterns
        """
        if not self.validate_credentials():
            raise ValueError("Google Vision API credentials required")
        
        try:
            thumbnail_analyses = []
            style_patterns = {}
            color_patterns = {}
            
            for url in thumbnail_urls:
                try:
                    analysis = await self.analyze_image_aesthetics(url)
                    thumbnail_analyses.append(analysis)
                    
                    # Aggregate style patterns
                    style = analysis['style_classification']
                    style_patterns[style] = style_patterns.get(style, 0) + 1
                    
                    # Aggregate color patterns
                    for color in analysis['dominant_colors'][:3]:  # Top 3 colors
                        color_key = f"rgb({color['red']},{color['green']},{color['blue']})"
                        color_patterns[color_key] = color_patterns.get(color_key, 0) + color['pixel_fraction']
                
                except Exception as e:
                    logging.warning(f"Thumbnail analysis failed for {url}: {e}")
            
            # Find winning patterns
            winning_patterns = {
                'most_common_style': max(style_patterns, key=style_patterns.get) if style_patterns else 'unknown',
                'dominant_color_palette': sorted(color_patterns.items(), key=lambda x: x[1], reverse=True)[:5],
                'average_aesthetic_score': sum(t['aesthetic_score'] for t in thumbnail_analyses) / len(thumbnail_analyses) if thumbnail_analyses else 0,
                'pattern_recommendations': self._generate_visual_recommendations(thumbnail_analyses),
                'total_analyzed': len(thumbnail_analyses),
                'analysis_method': 'google_vision_api'
            }
            
            return {
                'individual_analyses': thumbnail_analyses,
                'winning_patterns': winning_patterns
            }
            
        except Exception as e:
            logging.error(f"Thumbnail pattern analysis error: {e}")
            raise
    
    def _calculate_aesthetic_score(self, analysis: Dict[str, Any]) -> float:
        """
        Calculate aesthetic score based on visual elements
        """
        score = 0
        
        # Color harmony (more diverse colors = higher score up to a point)
        color_count = len(analysis['dominant_colors'])
        score += min(color_count * 10, 30)
        
        # Object composition (good object distribution)
        object_count = len(analysis['objects'])
        score += min(object_count * 5, 25)
        
        # Label relevance (high-confidence labels)
        relevant_labels = [l for l in analysis['labels'] if l['score'] > 0.8]
        score += min(len(relevant_labels) * 3, 25)
        
        # Text presence (some text can be good for engagement)
        if analysis['text_content']:
            score += 20
        
        return min(score, 100)
    
    def _classify_visual_style(self, analysis: Dict[str, Any]) -> str:
        """
        Classify visual style based on detected elements
        """
        labels = [l['description'].lower() for l in analysis['labels']]
        
        if any(word in labels for word in ['person', 'face', 'smile', 'human']):
            return 'people_focused'
        elif any(word in labels for word in ['product', 'technology', 'tool', 'equipment']):
            return 'product_focused'
        elif any(word in labels for word in ['text', 'font', 'design', 'graphic']):
            return 'text_heavy'
        elif any(word in labels for word in ['nature', 'landscape', 'building', 'architecture']):
            return 'environmental'
        else:
            return 'mixed_content'
    
    def _analyze_composition(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze image composition and layout
        """
        composition = {
            'object_distribution': 'unknown',
            'text_placement': 'none',
            'visual_weight': 'balanced'
        }
        
        objects = analysis['objects']
        if objects:
            # Analyze object positions
            center_objects = 0
            edge_objects = 0
            
            for obj in objects:
                # Calculate object center
                poly = obj['bounding_poly']
                if poly:
                    center_x = sum(v['x'] for v in poly) / len(poly)
                    center_y = sum(v['y'] for v in poly) / len(poly)
                    
                    if 0.3 <= center_x <= 0.7 and 0.3 <= center_y <= 0.7:
                        center_objects += 1
                    else:
                        edge_objects += 1
            
            if center_objects > edge_objects:
                composition['object_distribution'] = 'center_focused'
            else:
                composition['object_distribution'] = 'distributed'
        
        # Analyze text placement
        if analysis['text_content']:
            composition['text_placement'] = 'present'
        
        return composition
    
    def _generate_visual_recommendations(self, analyses: List[Dict[str, Any]]) -> List[str]:
        """
        Generate visual style recommendations based on pattern analysis
        """
        if not analyses:
            return []
        
        recommendations = []
        
        # Style recommendations
        styles = [a['style_classification'] for a in analyses]
        most_common_style = max(set(styles), key=styles.count)
        recommendations.append(f"Consider using {most_common_style} visual style")
        
        # Color recommendations
        all_colors = []
        for analysis in analyses:
            all_colors.extend(analysis['dominant_colors'][:2])
        
        if all_colors:
            avg_red = sum(c['red'] for c in all_colors) / len(all_colors)
            avg_green = sum(c['green'] for c in all_colors) / len(all_colors)
            avg_blue = sum(c['blue'] for c in all_colors) / len(all_colors)
            recommendations.append(f"Use colors similar to RGB({int(avg_red)},{int(avg_green)},{int(avg_blue)})")
        
        # Composition recommendations
        high_scoring = [a for a in analyses if a['aesthetic_score'] > 70]
        if high_scoring:
            recommendations.append("Include clear focal points and balanced composition")
        
        return recommendations
    
    def get_required_credentials_info(self) -> Dict[str, str]:
        """
        Return information about required Vision API credentials
        """
        return {
            'GOOGLE_APPLICATION_CREDENTIALS': 'Path to service account JSON file',
            'setup_instructions': 'https://cloud.google.com/vision/docs/setup',
            'required_apis': ['Vision API'],
            'service_account_roles': [
                'Cloud Vision API User'
            ]
        }