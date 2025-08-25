"""
Step 2: Validation Utilities for LinkedIn Scraper
URL validation, data sanitization, and input validation
"""

import re
import logging
from urllib.parse import urlparse, parse_qs
from typing import Optional, Dict, Any, List
from .exceptions import InvalidProfileURLError, ValidationError

logger = logging.getLogger(__name__)


class URLValidator:
    """LinkedIn URL validation and normalization"""
    
    # LinkedIn profile URL patterns
    LINKEDIN_PROFILE_PATTERNS = [
        r'^https?://(?:www\.)?linkedin\.com/in/([^/?]+)/?(?:\?.*)?$',
        r'^https?://(?:[a-z]{2}\.)?linkedin\.com/in/([^/?]+)/?(?:\?.*)?$',
    ]
    
    # Company page patterns
    LINKEDIN_COMPANY_PATTERNS = [
        r'^https?://(?:www\.)?linkedin\.com/company/([^/?]+)/?(?:\?.*)?$',
        r'^https?://(?:[a-z]{2}\.)?linkedin\.com/company/([^/?]+)/?(?:\?.*)?$',
    ]
    
    @classmethod
    def is_valid_linkedin_url(cls, url: str) -> bool:
        """
        Check if URL is a valid LinkedIn URL
        
        Args:
            url: URL to validate
            
        Returns:
            True if valid LinkedIn URL
        """
        if not url or not isinstance(url, str):
            return False
        
        # Check profile URLs
        for pattern in cls.LINKEDIN_PROFILE_PATTERNS:
            if re.match(pattern, url, re.IGNORECASE):
                return True
        
        # Check company URLs
        for pattern in cls.LINKEDIN_COMPANY_PATTERNS:
            if re.match(pattern, url, re.IGNORECASE):
                return True
        
        return False
    
    @classmethod
    def is_profile_url(cls, url: str) -> bool:
        """
        Check if URL is specifically a LinkedIn profile URL
        
        Args:
            url: URL to validate
            
        Returns:
            True if valid LinkedIn profile URL
        """
        if not url or not isinstance(url, str):
            return False
        
        for pattern in cls.LINKEDIN_PROFILE_PATTERNS:
            if re.match(pattern, url, re.IGNORECASE):
                return True
        
        return False
    
    @classmethod
    def normalize_profile_url(cls, url: str) -> str:
        """
        Normalize LinkedIn profile URL to standard format
        
        Args:
            url: URL to normalize
            
        Returns:
            Normalized URL
            
        Raises:
            InvalidProfileURLError: If URL is invalid
        """
        if not cls.is_profile_url(url):
            raise InvalidProfileURLError(f"Invalid LinkedIn profile URL: {url}")
        
        # Extract username from URL
        username = cls.extract_username(url)
        
        # Return normalized URL
        return f"https://www.linkedin.com/in/{username}/"
    
    @classmethod
    def extract_username(cls, url: str) -> str:
        """
        Extract username from LinkedIn profile URL
        
        Args:
            url: LinkedIn profile URL
            
        Returns:
            Username/slug from URL
            
        Raises:
            InvalidProfileURLError: If URL is invalid
        """
        if not cls.is_profile_url(url):
            raise InvalidProfileURLError(f"Invalid LinkedIn profile URL: {url}")
        
        for pattern in cls.LINKEDIN_PROFILE_PATTERNS:
            match = re.match(pattern, url, re.IGNORECASE)
            if match:
                return match.group(1)
        
        raise InvalidProfileURLError(f"Could not extract username from URL: {url}")
    
    @classmethod
    def validate_and_normalize(cls, url: str) -> str:
        """
        Validate and normalize LinkedIn profile URL
        
        Args:
            url: URL to validate and normalize
            
        Returns:
            Normalized URL
            
        Raises:
            InvalidProfileURLError: If URL is invalid
        """
        if not url:
            raise InvalidProfileURLError("URL cannot be empty")
        
        url = url.strip()
        
        # Add https:// if missing protocol
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        return cls.normalize_profile_url(url)


class DataValidator:
    """Data validation and sanitization utilities"""
    
    @staticmethod
    def sanitize_text(text: str, max_length: Optional[int] = None) -> str:
        """
        Sanitize text data by removing extra whitespace and normalizing
        
        Args:
            text: Text to sanitize
            max_length: Maximum allowed length
            
        Returns:
            Sanitized text
        """
        if not isinstance(text, str):
            return str(text) if text is not None else ""
        
        # Remove extra whitespace and normalize
        sanitized = ' '.join(text.split())
        
        # Remove invisible characters
        sanitized = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', sanitized)
        
        # Trim to max length if specified
        if max_length and len(sanitized) > max_length:
            sanitized = sanitized[:max_length].rstrip()
        
        return sanitized
    
    @staticmethod
    def validate_profile_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and sanitize profile data
        
        Args:
            data: Profile data dictionary
            
        Returns:
            Validated and sanitized data
            
        Raises:
            ValidationError: If data is invalid
        """
        if not isinstance(data, dict):
            raise ValidationError("Profile data must be a dictionary")
        
        validated_data = {}
        
        # Required fields
        required_fields = ['url', 'name', 'scraped_at']
        for field in required_fields:
            if field not in data:
                raise ValidationError(f"Missing required field: {field}")
        
        # Validate and sanitize each field
        validated_data['url'] = URLValidator.validate_and_normalize(data['url'])
        validated_data['name'] = DataValidator.sanitize_text(data['name'], max_length=100)
        
        if not validated_data['name']:
            raise ValidationError("Name cannot be empty")
        
        # Optional fields with validation
        optional_fields = {
            'headline': 200,
            'location': 100,
            'about': 5000,
        }
        
        for field, max_length in optional_fields.items():
            if field in data and data[field]:
                validated_data[field] = DataValidator.sanitize_text(data[field], max_length)
            else:
                validated_data[field] = ""
        
        # List fields
        list_fields = ['experience', 'education', 'skills']
        for field in list_fields:
            if field in data and isinstance(data[field], list):
                validated_data[field] = [
                    DataValidator.sanitize_text(item, max_length=500)
                    for item in data[field]
                    if item and isinstance(item, str)
                ][:20]  # Limit to 20 items
            else:
                validated_data[field] = []
        
        # Preserve scraped_at timestamp
        validated_data['scraped_at'] = data['scraped_at']
        
        return validated_data
    
    @staticmethod
    def calculate_data_quality_score(data: Dict[str, Any]) -> float:
        """
        Calculate data quality score based on completeness and validity
        
        Args:
            data: Profile data dictionary
            
        Returns:
            Quality score between 0.0 and 1.0
        """
        if not isinstance(data, dict):
            return 0.0
        
        score = 0.0
        max_score = 0.0
        
        # Core fields (higher weight)
        core_fields = {
            'name': 0.2,
            'headline': 0.15,
            'location': 0.1,
            'about': 0.15
        }
        
        for field, weight in core_fields.items():
            max_score += weight
            if field in data and data[field] and len(str(data[field]).strip()) > 0:
                # Bonus for longer, more complete data
                length_bonus = min(len(str(data[field])) / 100, 1.0) * 0.5
                score += weight * (0.5 + length_bonus)
        
        # List fields (medium weight)
        list_fields = {
            'experience': 0.2,
            'education': 0.1,
            'skills': 0.1
        }
        
        for field, weight in list_fields.items():
            max_score += weight
            if field in data and isinstance(data[field], list) and len(data[field]) > 0:
                # Score based on number of items
                item_score = min(len(data[field]) / 5, 1.0)  # Max score at 5+ items
                score += weight * item_score
        
        return min(score / max_score if max_score > 0 else 0.0, 1.0)


def validate_scraping_parameters(profile_url: str, output_path: Optional[str] = None,
                               headless: bool = True, timeout: int = 30) -> Dict[str, Any]:
    """
    Validate scraping parameters
    
    Args:
        profile_url: LinkedIn profile URL
        output_path: Output file path
        headless: Whether to run in headless mode
        timeout: Browser timeout in seconds
        
    Returns:
        Validated parameters dictionary
        
    Raises:
        ValidationError: If parameters are invalid
    """
    validated_params = {}
    
    # Validate URL
    try:
        validated_params['profile_url'] = URLValidator.validate_and_normalize(profile_url)
    except InvalidProfileURLError as e:
        raise ValidationError(f"Invalid profile URL: {e}")
    
    # Validate output path
    if output_path:
        if not isinstance(output_path, str):
            raise ValidationError("Output path must be a string")
        
        # Check file extension
        if not output_path.lower().endswith(('.json', '.csv', '.xlsx')):
            logger.warning(f"Unusual file extension for output: {output_path}")
        
        validated_params['output_path'] = output_path
    
    # Validate boolean parameters
    validated_params['headless'] = bool(headless)
    
    # Validate timeout
    if not isinstance(timeout, (int, float)) or timeout <= 0:
        raise ValidationError("Timeout must be a positive number")
    
    if timeout > 300:  # 5 minutes
        logger.warning(f"Very long timeout specified: {timeout} seconds")
    
    validated_params['timeout'] = int(timeout)
    
    return validated_params 