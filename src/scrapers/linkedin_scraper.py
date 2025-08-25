"""
Step 1 + 2: Enhanced LinkedIn Profile Scraper with Error Handling
A robust scraper with comprehensive error handling and retry mechanisms.
"""

import time
import json
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException, WebDriverException,
    SessionNotCreatedException, InvalidSessionIdException
)
from webdriver_manager.chrome import ChromeDriverManager
from fake_useragent import UserAgent

# Step 2: Import error handling utilities
from ..utils.exceptions import (
    LinkedInScraperError, NetworkError, RateLimitError, BrowserError,
    ProfileNotFoundError, ProfilePrivateError, DataExtractionError,
    CaptchaDetectedError, InvalidProfileURLError
)
from ..utils.retry import retry, with_circuit_breaker, exponential_backoff
from ..utils.validators import URLValidator, DataValidator, validate_scraping_parameters

logger = logging.getLogger(__name__)


class LinkedInScraper:
    """Enhanced LinkedIn profile scraper with robust error handling"""
    
    def __init__(self, headless=True, timeout=30, max_retries=3):
        """
        Initialize the scraper with Chrome WebDriver and error handling
        
        Args:
            headless: Run browser in headless mode
            timeout: Browser timeout in seconds
            max_retries: Maximum retry attempts for operations
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.driver = None
        self.wait = None
        
        try:
            self.driver = self._setup_driver(headless)
            self.wait = WebDriverWait(self.driver, timeout)
            logger.info("LinkedIn scraper initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize scraper: {e}")
            raise BrowserError(f"Failed to initialize browser: {e}")
    
    @retry(max_attempts=3, retry_on=(WebDriverException, SessionNotCreatedException))
    def _setup_driver(self, headless):
        """Setup Chrome WebDriver with options and retry logic"""
        options = Options()
        
        if headless:
            options.add_argument('--headless')
        
        # Enhanced anti-detection measures
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-plugins')
        options.add_argument('--disable-images')
        options.add_argument('--disable-javascript')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Set user agent
        try:
            ua = UserAgent()
            user_agent = ua.random
        except Exception:
            # Fallback user agent
            user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        
        options.add_argument(f'--user-agent={user_agent}')
        
        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            
            # Execute script to remove webdriver property
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Set window size for consistency
            driver.set_window_size(1920, 1080)
            
            logger.debug(f"WebDriver initialized with user agent: {user_agent[:50]}...")
            return driver
            
        except Exception as e:
            logger.error(f"Failed to setup WebDriver: {e}")
            raise BrowserError(f"WebDriver setup failed: {e}")
    
    def scrape_profile(self, profile_url):
        """
        Scrape profile with comprehensive error handling and validation
        
        Args:
            profile_url: LinkedIn profile URL to scrape
            
        Returns:
            Dictionary containing profile data or None if failed
            
        Raises:
            InvalidProfileURLError: If URL is invalid
            ProfileNotFoundError: If profile doesn't exist
            ProfilePrivateError: If profile is private
            NetworkError: If network issues occur
            RateLimitError: If rate limited
            DataExtractionError: If data extraction fails
        """
        try:
            # Step 2: Validate URL before scraping
            validated_url = URLValidator.validate_and_normalize(profile_url)
            logger.info(f"Scraping profile: {validated_url}")
            
            # Navigate to profile with retry logic
            self._navigate_to_profile(validated_url)
            
            # Check for common error conditions
            self._check_for_errors()
            
            # Extract profile data
            profile_data = self._extract_profile_data(validated_url)
            
            # Step 2: Validate extracted data
            validated_data = DataValidator.validate_profile_data(profile_data)
            
            # Calculate data quality score
            quality_score = DataValidator.calculate_data_quality_score(validated_data)
            validated_data['quality_score'] = quality_score
            
            logger.info(f"Successfully scraped profile with quality score: {quality_score:.2f}")
            return validated_data
            
        except (InvalidProfileURLError, ProfileNotFoundError, ProfilePrivateError) as e:
            logger.error(f"Profile error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error scraping profile: {e}")
            raise DataExtractionError(f"Failed to scrape profile: {e}")
    
    @retry(max_attempts=3, retry_on=(TimeoutException, WebDriverException))
    def _navigate_to_profile(self, profile_url):
        """Navigate to LinkedIn profile with retry logic"""
        try:
            self.driver.get(profile_url)
            
            # Wait for page to load
            self.wait.until(
                EC.any_of(
                    EC.presence_of_element_located((By.TAG_NAME, "main")),
                    EC.presence_of_element_located((By.CLASS_NAME, "profile")),
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
            )
            
            # Additional wait for dynamic content
            time.sleep(2)
            
            logger.debug(f"Successfully navigated to: {profile_url}")
            
        except TimeoutException:
            raise NetworkError(f"Timeout loading profile: {profile_url}")
        except WebDriverException as e:
            raise BrowserError(f"Browser error navigating to profile: {e}")
    
    def _check_for_errors(self):
        """Check for common LinkedIn error conditions"""
        page_source = self.driver.page_source.lower()
        current_url = self.driver.current_url.lower()
        
        # Check for CAPTCHA
        captcha_indicators = [
            'captcha', 'challenge', 'security check', 'verify you are human',
            'prove you are not a robot'
        ]
        
        for indicator in captcha_indicators:
            if indicator in page_source:
                raise CaptchaDetectedError(f"CAPTCHA detected: {indicator}")
        
        # Check for profile not found
        not_found_indicators = [
            'profile not found', 'user not found', 'page not found',
            'this profile doesn\'t exist', '404'
        ]
        
        for indicator in not_found_indicators:
            if indicator in page_source:
                raise ProfileNotFoundError("Profile does not exist or has been removed")
        
        # Check for private profile
        private_indicators = [
            'private profile', 'profile is private', 'sign in to view',
            'join linkedin to view', 'member\'s profile'
        ]
        
        for indicator in private_indicators:
            if indicator in page_source:
                raise ProfilePrivateError("Profile is private or requires authentication")
        
        # Check for rate limiting
        if 'linkedin.com/authwall' in current_url or 'authwall' in page_source:
            raise RateLimitError("Hit LinkedIn's authentication wall")
        
        # Check for blocked access
        if any(blocked in page_source for blocked in ['blocked', 'restricted', 'access denied']):
            raise RateLimitError("Access blocked by LinkedIn")
    
    def _extract_profile_data(self, profile_url):
        """Extract profile data with enhanced error handling"""
        profile_data = {
            'url': profile_url,
            'name': self._safe_extract(self._get_name, 'name'),
            'headline': self._safe_extract(self._get_headline, 'headline'),
            'location': self._safe_extract(self._get_location, 'location'),
            'about': self._safe_extract(self._get_about, 'about'),
            'experience': self._safe_extract(self._get_experience, 'experience', default=[]),
            'education': self._safe_extract(self._get_education, 'education', default=[]),
            'skills': self._safe_extract(self._get_skills, 'skills', default=[]),
            'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return profile_data
    
    def _safe_extract(self, extraction_func, field_name, default="Not found"):
        """
        Safely execute extraction function with error handling
        
        Args:
            extraction_func: Function to extract data
            field_name: Name of the field being extracted
            default: Default value if extraction fails
            
        Returns:
            Extracted data or default value
        """
        try:
            result = extraction_func()
            logger.debug(f"Successfully extracted {field_name}")
            return result
        except Exception as e:
            logger.warning(f"Failed to extract {field_name}: {e}")
            return default
    
    def _get_name(self):
        """Extract profile name with multiple fallback selectors"""
        name_selectors = [
            'h1.text-heading-xlarge',
            'h1[data-generated-suggestion-target]',
            '.pv-text-details__left-panel h1',
            '.pv-top-card--list h1',
            'h1.break-words'
        ]
        
        for selector in name_selectors:
            try:
                element = self.driver.find_element(By.CSS_SELECTOR, selector)
                name = element.text.strip()
                if name and len(name) > 0:
                    return name
            except NoSuchElementException:
                continue
        
        raise DataExtractionError("Could not extract profile name")
    
    def _get_headline(self):
        """Extract profile headline with multiple fallback selectors"""
        headline_selectors = [
            '.text-body-medium.break-words',
            '.pv-text-details__left-panel .text-body-medium',
            '[data-generated-suggestion-target] + .text-body-medium',
            '.pv-top-card--list .text-body-medium'
        ]
        
        for selector in headline_selectors:
            try:
                element = self.driver.find_element(By.CSS_SELECTOR, selector)
                headline = element.text.strip()
                if headline and 'contact info' not in headline.lower():
                    return headline
            except NoSuchElementException:
                continue
        
        return "Headline not found"
    
    def _get_location(self):
        """Extract location with multiple fallback selectors"""
        location_selectors = [
            '.text-body-small.inline.t-black--light.break-words',
            '.pv-text-details__left-panel .text-body-small',
            '.text-body-small.inline',
            '.pv-top-card--list .text-body-small'
        ]
        
        for selector in location_selectors:
            try:
                element = self.driver.find_element(By.CSS_SELECTOR, selector)
                location = element.text.strip()
                if location and 'contact info' not in location.lower():
                    return location
            except NoSuchElementException:
                continue
        
        return "Location not found"
    
    def _get_about(self):
        """Extract about section with multiple fallback selectors"""
        about_selectors = [
            '#about ~ * .display-flex .visually-hidden + span',
            '.pv-about-section .pv-about__summary-text',
            '[data-generated-suggestion-target="about"] ~ * span[aria-hidden="true"]',
            '.pv-about-section span[aria-hidden="true"]'
        ]
        
        for selector in about_selectors:
            try:
                element = self.driver.find_element(By.CSS_SELECTOR, selector)
                about = element.text.strip()
                if about and len(about) > 10:  # Minimum length check
                    return about
            except NoSuchElementException:
                continue
        
        return "About section not found"
    
    def _get_experience(self):
        """Extract experience with enhanced error handling"""
        experience_list = []
        experience_selectors = [
            '#experience ~ * .pvs-list__item--line-separated',
            '.pv-profile-section.experience .pv-entity__summary-info',
            '.experience-section .pv-entity__summary-info'
        ]
        
        for selector in experience_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements[:5]:  # Limit to 5 experiences
                    try:
                        text = element.text.strip()
                        if text and len(text) > 10:
                            experience_list.append(text)
                    except Exception as e:
                        logger.debug(f"Error extracting individual experience: {e}")
                        continue
                
                if experience_list:
                    break
                    
            except NoSuchElementException:
                continue
        
        return experience_list if experience_list else ["Experience not found"]
    
    def _get_education(self):
        """Extract education with enhanced error handling"""
        education_list = []
        education_selectors = [
            '#education ~ * .pvs-list__item--line-separated',
            '.pv-profile-section.education .pv-entity__summary-info',
            '.education-section .pv-entity__summary-info'
        ]
        
        for selector in education_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements[:5]:  # Limit to 5 education entries
                    try:
                        text = element.text.strip()
                        if text and len(text) > 5:
                            education_list.append(text)
                    except Exception as e:
                        logger.debug(f"Error extracting individual education: {e}")
                        continue
                
                if education_list:
                    break
                    
            except NoSuchElementException:
                continue
        
        return education_list if education_list else ["Education not found"]
    
    def _get_skills(self):
        """Extract skills with enhanced error handling"""
        skills_list = []
        skills_selectors = [
            '#skills ~ * .pvs-list__item--line-separated',
            '.pv-skill-category-entity__name span',
            '.skill-category-entity span'
        ]
        
        for selector in skills_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements[:15]:  # Limit to 15 skills
                    try:
                        text = element.text.strip()
                        if text and len(text) < 50 and len(text) > 1:  # Filter valid skills
                            skills_list.append(text)
                    except Exception as e:
                        logger.debug(f"Error extracting individual skill: {e}")
                        continue
                
                if skills_list:
                    break
                    
            except NoSuchElementException:
                continue
        
        return skills_list if skills_list else ["Skills not found"]
    
    def save_data(self, data, filename):
        """Save scraped data with error handling"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"Data saved successfully to {filename}")
        except Exception as e:
            logger.error(f"Failed to save data to {filename}: {e}")
            raise DataExtractionError(f"Failed to save data: {e}")
    
    def close(self):
        """Close the browser with error handling"""
        try:
            if self.driver:
                self.driver.quit()
                logger.debug("Browser closed successfully")
        except Exception as e:
            logger.warning(f"Error closing browser: {e}")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with error logging"""
        if exc_type:
            logger.error(f"Exception in scraper context: {exc_type.__name__}: {exc_val}")
        self.close() 