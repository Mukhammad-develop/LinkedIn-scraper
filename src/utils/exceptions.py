"""
Step 2: Custom Exception Classes for LinkedIn Scraper
Comprehensive error handling with specific exception types
"""


class LinkedInScraperError(Exception):
    """Base exception class for LinkedIn scraper errors"""
    
    def __init__(self, message, error_code=None, context=None):
        self.message = message
        self.error_code = error_code
        self.context = context or {}
        super().__init__(self.message)
    
    def __str__(self):
        base_msg = f"LinkedInScraperError: {self.message}"
        if self.error_code:
            base_msg += f" (Code: {self.error_code})"
        if self.context:
            base_msg += f" | Context: {self.context}"
        return base_msg


class NetworkError(LinkedInScraperError):
    """Network-related errors (connection, timeout, DNS)"""
    pass


class RateLimitError(LinkedInScraperError):
    """Rate limiting or anti-bot detection errors"""
    
    def __init__(self, message, retry_after=None, **kwargs):
        self.retry_after = retry_after
        super().__init__(message, **kwargs)


class AuthenticationError(LinkedInScraperError):
    """Authentication or access-related errors"""
    pass


class ProfileNotFoundError(LinkedInScraperError):
    """Profile does not exist or is not accessible"""
    pass


class ProfilePrivateError(LinkedInScraperError):
    """Profile exists but is private/restricted"""
    pass


class InvalidProfileURLError(LinkedInScraperError):
    """Invalid or malformed profile URL"""
    pass


class BrowserError(LinkedInScraperError):
    """Browser/WebDriver related errors"""
    pass


class DataExtractionError(LinkedInScraperError):
    """Errors during data extraction from profile"""
    pass


class ValidationError(LinkedInScraperError):
    """Data validation errors"""
    pass


class ConfigurationError(LinkedInScraperError):
    """Configuration or setup errors"""
    pass


class CaptchaDetectedError(RateLimitError):
    """CAPTCHA challenge detected"""
    
    def __init__(self, message="CAPTCHA challenge detected", **kwargs):
        super().__init__(message, **kwargs)


class MaxRetriesExceededError(LinkedInScraperError):
    """Maximum retry attempts exceeded"""
    
    def __init__(self, message, attempts=None, last_error=None, **kwargs):
        self.attempts = attempts
        self.last_error = last_error
        super().__init__(message, **kwargs) 