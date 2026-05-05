"""
Comprehensive form validation and data sanitization
"""

import re
from urllib.parse import urlparse
from typing import Dict, List, Optional, Tuple
import bleach
from markupsafe import Markup

class FormValidator:
    """Advanced form validation and sanitization"""
    
    # Allowed HTML tags for rich text (if needed)
    ALLOWED_TAGS = ['b', 'i', 'u', 'em', 'strong', 'p', 'br']
    
    # Common malicious patterns
    MALICIOUS_PATTERNS = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'on\w+\s*=',
        r'data:text/html',
        r'vbscript:',
    ]
    
    @staticmethod
    def validate_campaign_form(form_data: Dict) -> Tuple[bool, Dict[str, List[str]]]:
        """Comprehensive campaign form validation"""
        errors = {}
        
        # Required fields validation
        required_fields = ['title', 'business_url', 'campaign_goal']
        for field in required_fields:
            value = form_data.get(field, '').strip()
            if not value:
                errors.setdefault(field, []).append(f"{field.replace('_', ' ').title()} is required")
        
        # Title validation
        title = form_data.get('title', '').strip()
        if title:
            if len(title) < 3:
                errors.setdefault('title', []).append("Title must be at least 3 characters long")
            elif len(title) > 200:
                errors.setdefault('title', []).append("Title cannot exceed 200 characters")
            elif FormValidator._contains_malicious_content(title):
                errors.setdefault('title', []).append("Title contains invalid characters")
        
        # Business URL validation
        business_url = form_data.get('business_url', '').strip()
        if business_url:
            if not FormValidator.validate_url(business_url):
                errors.setdefault('business_url', []).append("Please enter a valid URL (include http:// or https://)")
        
        # Campaign goal validation
        campaign_goal = form_data.get('campaign_goal', '').strip()
        valid_goals = ['brand_awareness', 'lead_generation', 'sales', 'engagement', 'traffic']
        if campaign_goal and campaign_goal not in valid_goals:
            errors.setdefault('campaign_goal', []).append("Please select a valid campaign goal")
        
        # Target audience validation
        target_audience = form_data.get('target_audience', '').strip()
        if target_audience and len(target_audience) > 500:
            errors.setdefault('target_audience', []).append("Target audience description cannot exceed 500 characters")
        
        # Additional information validation
        additional_info = form_data.get('additional_info', '').strip()
        if additional_info:
            if len(additional_info) > 2000:
                errors.setdefault('additional_info', []).append("Additional information cannot exceed 2000 characters")
            elif FormValidator._contains_malicious_content(additional_info):
                errors.setdefault('additional_info', []).append("Additional information contains invalid content")
        
        # Industry validation (if provided)
        industry = form_data.get('industry', '').strip()
        valid_industries = [
            'technology', 'healthcare', 'finance', 'retail', 'education', 
            'real-estate', 'consulting', 'manufacturing', 'other'
        ]
        if industry and industry not in valid_industries:
            errors.setdefault('industry', []).append("Please select a valid industry")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_revision_form(form_data: Dict) -> Tuple[bool, Dict[str, List[str]]]:
        """Validate revision request form"""
        errors = {}
        
        # User notes validation
        user_notes = form_data.get('user_notes', '').strip()
        if not user_notes:
            errors.setdefault('user_notes', []).append("Please provide feedback or revision notes")
        elif len(user_notes) < 10:
            errors.setdefault('user_notes', []).append("Please provide more detailed feedback (at least 10 characters)")
        elif len(user_notes) > 2000:
            errors.setdefault('user_notes', []).append("Feedback cannot exceed 2000 characters")
        elif FormValidator._contains_malicious_content(user_notes):
            errors.setdefault('user_notes', []).append("Feedback contains invalid content")
        
        # Revision type validation
        revision_type = form_data.get('revision_type', '').strip()
        valid_types = ['text', 'image', 'video', 'all']
        if revision_type and revision_type not in valid_types:
            errors.setdefault('revision_type', []).append("Please select a valid revision type")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_profile_form(form_data: Dict) -> Tuple[bool, Dict[str, List[str]]]:
        """Validate user profile form"""
        errors = {}
        
        # Username validation
        username = form_data.get('username', '').strip()
        if username:
            if len(username) < 3:
                errors.setdefault('username', []).append("Username must be at least 3 characters long")
            elif len(username) > 50:
                errors.setdefault('username', []).append("Username cannot exceed 50 characters")
            elif not re.match(r'^[a-zA-Z0-9_-]+$', username):
                errors.setdefault('username', []).append("Username can only contain letters, numbers, underscores, and hyphens")
        
        # Full name validation
        full_name = form_data.get('full_name', '').strip()
        if full_name:
            if len(full_name) > 100:
                errors.setdefault('full_name', []).append("Full name cannot exceed 100 characters")
            elif FormValidator._contains_malicious_content(full_name):
                errors.setdefault('full_name', []).append("Full name contains invalid characters")
        
        # Company name validation
        company_name = form_data.get('company_name', '').strip()
        if company_name:
            if len(company_name) > 100:
                errors.setdefault('company_name', []).append("Company name cannot exceed 100 characters")
            elif FormValidator._contains_malicious_content(company_name):
                errors.setdefault('company_name', []).append("Company name contains invalid characters")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def sanitize_text_input(text: str, allow_html: bool = False) -> str:
        """Sanitize text input to prevent XSS and injection attacks"""
        if not text:
            return ""
        
        # Remove null bytes and control characters
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
        
        if allow_html:
            # Use bleach to clean HTML but allow safe tags
            text = bleach.clean(text, tags=FormValidator.ALLOWED_TAGS, strip=True)
        else:
            # Remove all HTML tags
            text = bleach.clean(text, tags=[], strip=True)
        
        # Additional sanitization
        text = text.strip()
        
        return text
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate URL format and scheme"""
        try:
            parsed = urlparse(url)
            return all([
                parsed.scheme in ['http', 'https'],
                parsed.netloc,
                '.' in parsed.netloc,
                len(parsed.netloc) > 3
            ])
        except:
            return False
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_pattern, email))
    
    @staticmethod
    def _contains_malicious_content(text: str) -> bool:
        """Check for malicious patterns in text"""
        text_lower = text.lower()
        
        for pattern in FormValidator.MALICIOUS_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True
        
        # Check for SQL injection patterns
        sql_patterns = ['union select', 'drop table', 'insert into', 'delete from', '--', ';--']
        for pattern in sql_patterns:
            if pattern in text_lower:
                return True
        
        return False
    
    @staticmethod
    def sanitize_form_data(form_data: Dict) -> Dict:
        """Sanitize all form data"""
        sanitized = {}
        
        for key, value in form_data.items():
            if isinstance(value, str):
                # Determine if HTML should be allowed for certain fields
                allow_html = key in ['additional_info', 'user_notes']
                sanitized[key] = FormValidator.sanitize_text_input(value, allow_html)
            else:
                sanitized[key] = value
        
        return sanitized


class FileValidator:
    """Validate uploaded files"""
    
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png', 'gif'}
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
    
    @staticmethod
    def validate_file(file) -> Tuple[bool, str]:
        """Validate uploaded file"""
        if not file or not file.filename:
            return False, "No file selected"
        
        # Check file extension
        if '.' not in file.filename:
            return False, "File must have an extension"
        
        ext = file.filename.rsplit('.', 1)[1].lower()
        if ext not in FileValidator.ALLOWED_EXTENSIONS:
            return False, f"File type not allowed. Allowed types: {', '.join(FileValidator.ALLOWED_EXTENSIONS)}"
        
        # Check file size (if possible)
        try:
            file.seek(0, 2)  # Seek to end
            size = file.tell()
            file.seek(0)     # Seek back to beginning
            
            if size > FileValidator.MAX_FILE_SIZE:
                return False, f"File too large. Maximum size: {FileValidator.MAX_FILE_SIZE // (1024*1024)}MB"
        except:
            pass  # Size check failed, but continue
        
        return True, "File is valid"
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename for safe storage"""
        if not filename:
            return "unnamed_file"
        
        # Remove path components
        filename = filename.split('/')[-1].split('\\')[-1]
        
        # Replace unsafe characters
        filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
        
        # Limit length
        if len(filename) > 100:
            name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
            filename = name[:90] + ('.' + ext if ext else '')
        
        return filename


# Export main classes
__all__ = ['FormValidator', 'FileValidator']