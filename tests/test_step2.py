"""
Test suite for Step 2: Error Handling and Retry Mechanisms
"""

import unittest
import sys
import os
import time
from unittest.mock import Mock, patch, MagicMock

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.exceptions import (
    LinkedInScraperError, NetworkError, RateLimitError, BrowserError,
    ProfileNotFoundError, ProfilePrivateError, InvalidProfileURLError,
    DataExtractionError, ValidationError, CaptchaDetectedError,
    MaxRetriesExceededError
)
from utils.retry import retry, exponential_backoff, CircuitBreaker
from utils.validators import URLValidator, DataValidator, validate_scraping_parameters


class TestExceptions(unittest.TestCase):
    """Test custom exception classes"""
    
    def test_base_exception(self):
        """Test base LinkedInScraperError"""
        error = LinkedInScraperError("Test message", error_code="TEST_001", context={"url": "test"})
        
        self.assertEqual(error.message, "Test message")
        self.assertEqual(error.error_code, "TEST_001")
        self.assertEqual(error.context["url"], "test")
        self.assertIn("TEST_001", str(error))
    
    def test_rate_limit_error(self):
        """Test RateLimitError with retry_after"""
        error = RateLimitError("Rate limited", retry_after=60)
        self.assertEqual(error.retry_after, 60)
    
    def test_max_retries_exceeded(self):
        """Test MaxRetriesExceededError with attempts"""
        last_error = NetworkError("Connection failed")
        error = MaxRetriesExceededError("Max retries", attempts=3, last_error=last_error)
        
        self.assertEqual(error.attempts, 3)
        self.assertEqual(error.last_error, last_error)


class TestRetryMechanism(unittest.TestCase):
    """Test retry decorator and exponential backoff"""
    
    def test_exponential_backoff(self):
        """Test exponential backoff calculation"""
        backoff_func = exponential_backoff(base_delay=1.0, max_delay=10.0)
        
        # Test increasing delays
        delay1 = backoff_func(0)  # First attempt
        delay2 = backoff_func(1)  # Second attempt
        delay3 = backoff_func(2)  # Third attempt
        
        self.assertGreaterEqual(delay1, 0.1)  # Minimum delay
        self.assertGreater(delay2, delay1)    # Increasing
        self.assertGreater(delay3, delay2)    # Increasing
        self.assertLessEqual(delay3, 10.0)    # Max delay
    
    def test_successful_retry(self):
        """Test retry decorator with successful execution"""
        call_count = 0
        
        @retry(max_attempts=3)
        def sometimes_fails():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise NetworkError("Network failed")
            return "success"
        
        result = sometimes_fails()
        self.assertEqual(result, "success")
        self.assertEqual(call_count, 2)
    
    def test_retry_exhaustion(self):
        """Test retry decorator when all attempts fail"""
        call_count = 0
        
        @retry(max_attempts=2, delay_func=lambda x: 0.01)  # Fast retry for testing
        def always_fails():
            nonlocal call_count
            call_count += 1
            raise NetworkError("Always fails")
        
        with self.assertRaises(MaxRetriesExceededError):
            always_fails()
        
        self.assertEqual(call_count, 2)
    
    def test_non_retryable_error(self):
        """Test that non-retryable errors are not retried"""
        call_count = 0
        
        @retry(max_attempts=3, stop_on=(KeyboardInterrupt,))
        def raises_keyboard_interrupt():
            nonlocal call_count
            call_count += 1
            raise KeyboardInterrupt("User interrupted")
        
        with self.assertRaises(KeyboardInterrupt):
            raises_keyboard_interrupt()
        
        self.assertEqual(call_count, 1)  # Should not retry


class TestCircuitBreaker(unittest.TestCase):
    """Test circuit breaker pattern"""
    
    def test_circuit_breaker_open(self):
        """Test circuit breaker opens after failures"""
        call_count = 0
        
        @CircuitBreaker(failure_threshold=2, recovery_timeout=0.1, expected_exception=ValueError)
        def failing_function():
            nonlocal call_count
            call_count += 1
            raise ValueError("Function failed")
        
        # First two calls should fail normally
        with self.assertRaises(ValueError):
            failing_function()
        with self.assertRaises(ValueError):
            failing_function()
        
        # Third call should trigger circuit breaker
        with self.assertRaises(LinkedInScraperError):
            failing_function()
        
        self.assertEqual(call_count, 2)  # Circuit breaker prevents third call
    
    def test_circuit_breaker_recovery(self):
        """Test circuit breaker recovery after timeout"""
        call_count = 0
        
        breaker = CircuitBreaker(failure_threshold=1, recovery_timeout=0.01, expected_exception=ValueError)
        
        @breaker
        def sometimes_works():
            nonlocal call_count
            call_count += 1
            if call_count <= 1:
                raise ValueError("First call fails")
            return "success"
        
        # First call fails, opens circuit
        with self.assertRaises(ValueError):
            sometimes_works()
        
        # Immediate second call blocked by circuit breaker
        with self.assertRaises(LinkedInScraperError):
            sometimes_works()
        
        # Wait for recovery timeout
        time.sleep(0.02)
        
        # Should work after recovery
        result = sometimes_works()
        self.assertEqual(result, "success")


class TestURLValidator(unittest.TestCase):
    """Test URL validation utilities"""
    
    def test_valid_linkedin_urls(self):
        """Test validation of valid LinkedIn URLs"""
        valid_urls = [
            "https://www.linkedin.com/in/username",
            "https://linkedin.com/in/username/",
            "http://www.linkedin.com/in/username?param=value",
            "https://de.linkedin.com/in/username",
        ]
        
        for url in valid_urls:
            with self.subTest(url=url):
                self.assertTrue(URLValidator.is_valid_linkedin_url(url))
                self.assertTrue(URLValidator.is_profile_url(url))
    
    def test_invalid_urls(self):
        """Test validation of invalid URLs"""
        invalid_urls = [
            "https://facebook.com/username",
            "https://linkedin.com/company/test",  # Company, not profile
            "not-a-url",
            "",
            None,
            "https://linkedin.com/in/",  # Missing username
        ]
        
        for url in invalid_urls:
            with self.subTest(url=url):
                self.assertFalse(URLValidator.is_profile_url(url))
    
    def test_url_normalization(self):
        """Test URL normalization"""
        test_cases = [
            ("linkedin.com/in/username", "https://www.linkedin.com/in/username/"),
            ("https://linkedin.com/in/username/", "https://www.linkedin.com/in/username/"),
            ("https://www.linkedin.com/in/username?param=value", "https://www.linkedin.com/in/username/"),
        ]
        
        for input_url, expected in test_cases:
            with self.subTest(input_url=input_url):
                result = URLValidator.validate_and_normalize(input_url)
                self.assertEqual(result, expected)
    
    def test_username_extraction(self):
        """Test username extraction from URLs"""
        test_cases = [
            ("https://www.linkedin.com/in/johndoe", "johndoe"),
            ("https://linkedin.com/in/jane-smith/", "jane-smith"),
            ("https://de.linkedin.com/in/user123?param=value", "user123"),
        ]
        
        for url, expected_username in test_cases:
            with self.subTest(url=url):
                username = URLValidator.extract_username(url)
                self.assertEqual(username, expected_username)


class TestDataValidator(unittest.TestCase):
    """Test data validation utilities"""
    
    def test_text_sanitization(self):
        """Test text sanitization"""
        test_cases = [
            ("  Extra   spaces  ", "Extra spaces"),
            ("Text\nwith\nnewlines", "Text with newlines"),
            ("Text\x00with\x08invisible\x1fchars", "Textwithvisiblechars"),
            ("Very long text" * 100, "Very long text" * 10),  # Should be trimmed
        ]
        
        for input_text, expected in test_cases:
            with self.subTest(input_text=input_text[:50]):
                if len(expected) > 100:
                    # Test with max_length for long text
                    result = DataValidator.sanitize_text(input_text, max_length=100)
                    self.assertLessEqual(len(result), 100)
                else:
                    result = DataValidator.sanitize_text(input_text)
                    self.assertEqual(result, expected)
    
    def test_profile_data_validation(self):
        """Test profile data validation"""
        valid_data = {
            'url': 'https://linkedin.com/in/test',
            'name': 'Test User',
            'headline': 'Software Engineer',
            'location': 'San Francisco',
            'about': 'About text',
            'experience': ['Job 1', 'Job 2'],
            'education': ['School 1'],
            'skills': ['Python', 'JavaScript'],
            'scraped_at': '2024-01-01 12:00:00'
        }
        
        result = DataValidator.validate_profile_data(valid_data)
        
        self.assertEqual(result['name'], 'Test User')
        self.assertEqual(result['url'], 'https://www.linkedin.com/in/test/')
        self.assertEqual(len(result['experience']), 2)
        self.assertEqual(len(result['skills']), 2)
    
    def test_invalid_profile_data(self):
        """Test validation of invalid profile data"""
        # Missing required fields
        invalid_data = {
            'name': 'Test User'
            # Missing 'url' and 'scraped_at'
        }
        
        with self.assertRaises(ValidationError):
            DataValidator.validate_profile_data(invalid_data)
        
        # Empty name
        invalid_data2 = {
            'url': 'https://linkedin.com/in/test',
            'name': '',
            'scraped_at': '2024-01-01'
        }
        
        with self.assertRaises(ValidationError):
            DataValidator.validate_profile_data(invalid_data2)
    
    def test_data_quality_score(self):
        """Test data quality scoring"""
        # High quality data
        high_quality = {
            'name': 'John Doe',
            'headline': 'Senior Software Engineer at Tech Corp',
            'location': 'San Francisco, CA',
            'about': 'Experienced software engineer with 10+ years...' * 5,
            'experience': ['Job 1', 'Job 2', 'Job 3', 'Job 4', 'Job 5'],
            'education': ['University 1', 'University 2'],
            'skills': ['Python', 'JavaScript', 'React', 'Node.js', 'AWS']
        }
        
        score = DataValidator.calculate_data_quality_score(high_quality)
        self.assertGreater(score, 0.8)
        
        # Low quality data
        low_quality = {
            'name': 'User',
            'headline': '',
            'location': '',
            'about': '',
            'experience': [],
            'education': [],
            'skills': []
        }
        
        score = DataValidator.calculate_data_quality_score(low_quality)
        self.assertLess(score, 0.3)


class TestParameterValidation(unittest.TestCase):
    """Test scraping parameter validation"""
    
    def test_valid_parameters(self):
        """Test validation of valid parameters"""
        result = validate_scraping_parameters(
            profile_url="https://linkedin.com/in/test",
            output_path="data/test.json",
            headless=True,
            timeout=30
        )
        
        self.assertEqual(result['profile_url'], 'https://www.linkedin.com/in/test/')
        self.assertEqual(result['output_path'], 'data/test.json')
        self.assertTrue(result['headless'])
        self.assertEqual(result['timeout'], 30)
    
    def test_invalid_timeout(self):
        """Test validation of invalid timeout"""
        with self.assertRaises(ValidationError):
            validate_scraping_parameters(
                profile_url="https://linkedin.com/in/test",
                timeout=-5
            )
        
        with self.assertRaises(ValidationError):
            validate_scraping_parameters(
                profile_url="https://linkedin.com/in/test",
                timeout="not-a-number"
            )


if __name__ == '__main__':
    print("🧪 Running Step 2 Tests: Error Handling and Retry Mechanisms")
    print("-" * 60)
    
    # Run tests with verbose output
    unittest.main(verbosity=2, exit=False)
    
    print("\n✅ Step 2 tests completed!")
    print("💡 These tests verify error handling, retry mechanisms, and validation utilities.") 