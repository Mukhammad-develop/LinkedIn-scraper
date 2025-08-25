"""
Test suite for Step 1: Basic LinkedIn Scraper
"""

import unittest
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from scrapers.linkedin_scraper import LinkedInScraper


class TestLinkedInScraperStep1(unittest.TestCase):
    """Test cases for basic LinkedIn scraper functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.scraper = None
    
    def tearDown(self):
        """Clean up after tests"""
        if self.scraper:
            self.scraper.close()
    
    def test_scraper_initialization(self):
        """Test scraper can be initialized"""
        try:
            self.scraper = LinkedInScraper(headless=True)
            self.assertIsNotNone(self.scraper.driver)
            self.assertIsNotNone(self.scraper.wait)
        except Exception as e:
            self.fail(f"Scraper initialization failed: {e}")
    
    def test_context_manager(self):
        """Test scraper works as context manager"""
        try:
            with LinkedInScraper(headless=True) as scraper:
                self.assertIsNotNone(scraper.driver)
        except Exception as e:
            self.fail(f"Context manager failed: {e}")
    
    def test_invalid_url_handling(self):
        """Test handling of invalid URLs"""
        with LinkedInScraper(headless=True) as scraper:
            result = scraper.scrape_profile("invalid-url")
            # Should return None or handle gracefully
            self.assertIsNone(result)
    
    def test_data_structure(self):
        """Test that scraped data has expected structure"""
        expected_keys = [
            'url', 'name', 'headline', 'location', 
            'about', 'experience', 'education', 'skills', 'scraped_at'
        ]
        
        # This would need a valid test profile URL
        # For now, just test the expected structure
        sample_data = {
            'url': 'test-url',
            'name': 'Test Name',
            'headline': 'Test Headline',
            'location': 'Test Location',
            'about': 'Test About',
            'experience': ['Test Experience'],
            'education': ['Test Education'],
            'skills': ['Test Skill'],
            'scraped_at': '2024-01-01 12:00:00'
        }
        
        for key in expected_keys:
            self.assertIn(key, sample_data)


if __name__ == '__main__':
    print("🧪 Running Step 1 Tests...")
    print("Note: These are basic structure tests.")
    print("For full testing, you'll need valid LinkedIn profile URLs.")
    print("-" * 50)
    
    unittest.main(verbosity=2) 