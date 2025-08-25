"""
Step 1: Basic LinkedIn Profile Scraper
A simple scraper that extracts basic profile information from LinkedIn profiles.
"""

import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from fake_useragent import UserAgent


class LinkedInScraper:
    """Basic LinkedIn profile scraper for Step 1"""
    
    def __init__(self, headless=True, timeout=30):
        """Initialize the scraper with Chrome WebDriver"""
        self.timeout = timeout
        self.driver = self._setup_driver(headless)
        self.wait = WebDriverWait(self.driver, timeout)
        
    def _setup_driver(self, headless):
        """Setup Chrome WebDriver with options"""
        options = Options()
        
        if headless:
            options.add_argument('--headless')
        
        # Anti-detection measures
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Set user agent
        ua = UserAgent()
        options.add_argument(f'--user-agent={ua.random}')
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        # Execute script to remove webdriver property
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver
    
    def scrape_profile(self, profile_url):
        """Scrape basic information from a LinkedIn profile"""
        try:
            print(f"Scraping profile: {profile_url}")
            self.driver.get(profile_url)
            
            # Wait for page to load
            time.sleep(3)
            
            profile_data = {
                'url': profile_url,
                'name': self._get_name(),
                'headline': self._get_headline(),
                'location': self._get_location(),
                'about': self._get_about(),
                'experience': self._get_experience(),
                'education': self._get_education(),
                'skills': self._get_skills(),
                'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            return profile_data
            
        except Exception as e:
            print(f"Error scraping profile: {str(e)}")
            return None
    
    def _get_name(self):
        """Extract profile name"""
        try:
            name_selectors = [
                'h1.text-heading-xlarge',
                'h1[data-generated-suggestion-target]',
                '.pv-text-details__left-panel h1'
            ]
            
            for selector in name_selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    return element.text.strip()
                except NoSuchElementException:
                    continue
            
            return "Name not found"
        except Exception:
            return "Name not found"
    
    def _get_headline(self):
        """Extract profile headline"""
        try:
            headline_selectors = [
                '.text-body-medium.break-words',
                '.pv-text-details__left-panel .text-body-medium',
                '[data-generated-suggestion-target] + .text-body-medium'
            ]
            
            for selector in headline_selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    return element.text.strip()
                except NoSuchElementException:
                    continue
            
            return "Headline not found"
        except Exception:
            return "Headline not found"
    
    def _get_location(self):
        """Extract location information"""
        try:
            location_selectors = [
                '.text-body-small.inline.t-black--light.break-words',
                '.pv-text-details__left-panel .text-body-small',
                '.text-body-small.inline'
            ]
            
            for selector in location_selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    text = element.text.strip()
                    if text and 'contact info' not in text.lower():
                        return text
                except NoSuchElementException:
                    continue
            
            return "Location not found"
        except Exception:
            return "Location not found"
    
    def _get_about(self):
        """Extract about section"""
        try:
            about_selectors = [
                '#about ~ * .display-flex .visually-hidden + span',
                '.pv-about-section .pv-about__summary-text',
                '[data-generated-suggestion-target="about"] ~ * span[aria-hidden="true"]'
            ]
            
            for selector in about_selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    return element.text.strip()
                except NoSuchElementException:
                    continue
            
            return "About section not found"
        except Exception:
            return "About section not found"
    
    def _get_experience(self):
        """Extract experience information (simplified)"""
        try:
            experience_list = []
            experience_selectors = [
                '#experience ~ * .pvs-list__item--line-separated',
                '.pv-profile-section.experience .pv-entity__summary-info'
            ]
            
            for selector in experience_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements[:3]:  # Get first 3 experiences
                        text = element.text.strip()
                        if text:
                            experience_list.append(text)
                    break
                except NoSuchElementException:
                    continue
            
            return experience_list if experience_list else ["Experience not found"]
        except Exception:
            return ["Experience not found"]
    
    def _get_education(self):
        """Extract education information (simplified)"""
        try:
            education_list = []
            education_selectors = [
                '#education ~ * .pvs-list__item--line-separated',
                '.pv-profile-section.education .pv-entity__summary-info'
            ]
            
            for selector in education_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements[:3]:  # Get first 3 education entries
                        text = element.text.strip()
                        if text:
                            education_list.append(text)
                    break
                except NoSuchElementException:
                    continue
            
            return education_list if education_list else ["Education not found"]
        except Exception:
            return ["Education not found"]
    
    def _get_skills(self):
        """Extract skills information (simplified)"""
        try:
            skills_list = []
            skills_selectors = [
                '#skills ~ * .pvs-list__item--line-separated',
                '.pv-skill-category-entity__name span'
            ]
            
            for selector in skills_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements[:10]:  # Get first 10 skills
                        text = element.text.strip()
                        if text and len(text) < 50:  # Filter out long descriptions
                            skills_list.append(text)
                    break
                except NoSuchElementException:
                    continue
            
            return skills_list if skills_list else ["Skills not found"]
        except Exception:
            return ["Skills not found"]
    
    def save_data(self, data, filename):
        """Save scraped data to JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"Data saved to {filename}")
        except Exception as e:
            print(f"Error saving data: {str(e)}")
    
    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close() 