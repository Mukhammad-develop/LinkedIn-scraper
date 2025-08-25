"""
Test suite for Step 3: Data Validation and Sanitization
"""

import unittest
import sys
import os
from datetime import datetime

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.models import ProfileData, ScrapingConfig, DataQuality, ExperienceEntry, EducationEntry
from utils.data_quality import DataQualityAnalyzer, QualityReport, QualityIssue, IssueType, Severity
from pydantic import ValidationError


class TestPydanticModels(unittest.TestCase):
    """Test Pydantic models for data validation"""
    
    def test_profile_data_valid(self):
        """Test ProfileData with valid data"""
        valid_data = {
            'url': 'https://linkedin.com/in/test-user',
            'name': 'John Doe',
            'headline': 'Software Engineer at Tech Corp',
            'location': 'San Francisco, CA',
            'about': 'Experienced software engineer with 5+ years of experience...',
            'experience': ['Software Engineer at Tech Corp', 'Junior Developer at StartupXYZ'],
            'education': ['BS Computer Science - Stanford University'],
            'skills': ['Python', 'JavaScript', 'React', 'Node.js'],
            'scraped_at': '2024-01-15 14:30:00'
        }
        
        profile = ProfileData(**valid_data)
        
        self.assertEqual(profile.name, 'John Doe')
        self.assertEqual(profile.url, 'https://linkedin.com/in/test-user/')
        self.assertIsInstance(profile.quality_score, float)
        self.assertIsInstance(profile.quality_level, DataQuality)
        self.assertIsInstance(profile.data_completeness, float)
        self.assertGreater(profile.quality_score, 0.7)  # Should be high quality
    
    def test_profile_data_url_normalization(self):
        """Test URL normalization in ProfileData"""
        test_cases = [
            ('linkedin.com/in/user', 'https://linkedin.com/in/user/'),
            ('https://linkedin.com/in/user/', 'https://linkedin.com/in/user/'),
            ('http://www.linkedin.com/in/user?param=1', 'http://www.linkedin.com/in/user?param=1'),
        ]
        
        for input_url, expected_url in test_cases:
            with self.subTest(input_url=input_url):
                profile = ProfileData(
                    url=input_url,
                    name='Test User',
                    scraped_at='2024-01-15'
                )
                self.assertEqual(profile.url, expected_url)
    
    def test_profile_data_invalid_url(self):
        """Test ProfileData with invalid URLs"""
        invalid_urls = [
            'https://facebook.com/user',
            'not-a-url',
            '',
            'https://example.com'
        ]
        
        for invalid_url in invalid_urls:
            with self.subTest(url=invalid_url):
                with self.assertRaises(ValidationError):
                    ProfileData(
                        url=invalid_url,
                        name='Test User',
                        scraped_at='2024-01-15'
                    )
    
    def test_profile_data_name_validation(self):
        """Test name validation and sanitization"""
        test_cases = [
            ('  John   Doe  ', 'John Doe'),
            ('Jane\nSmith', 'Jane Smith'),
            ('Bob\t\tJohnson', 'Bob Johnson'),
        ]
        
        for input_name, expected_name in test_cases:
            with self.subTest(name=input_name):
                profile = ProfileData(
                    url='https://linkedin.com/in/test',
                    name=input_name,
                    scraped_at='2024-01-15'
                )
                self.assertEqual(profile.name, expected_name)
    
    def test_profile_data_empty_name(self):
        """Test ProfileData with empty name"""
        invalid_names = ['', '   ', None]
        
        for invalid_name in invalid_names:
            with self.subTest(name=invalid_name):
                with self.assertRaises(ValidationError):
                    ProfileData(
                        url='https://linkedin.com/in/test',
                        name=invalid_name,
                        scraped_at='2024-01-15'
                    )
    
    def test_profile_data_skills_deduplication(self):
        """Test skills deduplication"""
        profile = ProfileData(
            url='https://linkedin.com/in/test',
            name='Test User',
            skills=['Python', 'python', 'PYTHON', 'JavaScript', 'Python'],
            scraped_at='2024-01-15'
        )
        
        # Should remove case-insensitive duplicates
        unique_skills = set(skill.lower() for skill in profile.skills)
        self.assertLessEqual(len(unique_skills), 2)  # python and javascript
    
    def test_experience_entry_model(self):
        """Test ExperienceEntry model"""
        experience = ExperienceEntry(
            title='Software Engineer',
            company='Tech Corp',
            duration='2020 - Present',
            location='San Francisco, CA',
            description='Developed web applications...',
            raw_text='Software Engineer at Tech Corp (2020 - Present) - San Francisco, CA'
        )
        
        self.assertEqual(experience.title, 'Software Engineer')
        self.assertEqual(experience.company, 'Tech Corp')
        self.assertIsNotNone(experience.raw_text)
    
    def test_experience_entry_invalid(self):
        """Test ExperienceEntry with invalid data"""
        with self.assertRaises(ValidationError):
            ExperienceEntry(raw_text='')  # Empty raw_text should fail
        
        with self.assertRaises(ValidationError):
            ExperienceEntry(raw_text=None)  # None raw_text should fail
    
    def test_education_entry_model(self):
        """Test EducationEntry model"""
        education = EducationEntry(
            institution='Stanford University',
            degree='Bachelor of Science',
            field_of_study='Computer Science',
            duration='2016 - 2020',
            raw_text='BS Computer Science - Stanford University (2016-2020)'
        )
        
        self.assertEqual(education.institution, 'Stanford University')
        self.assertEqual(education.degree, 'Bachelor of Science')
        self.assertIsNotNone(education.raw_text)
    
    def test_scraping_config_model(self):
        """Test ScrapingConfig model"""
        config = ScrapingConfig(
            profile_url='https://linkedin.com/in/test',
            output_path='data/test.json',
            headless=True,
            timeout=60,
            max_retries=5
        )
        
        self.assertEqual(config.profile_url, 'https://linkedin.com/in/test/')
        self.assertEqual(config.output_path, 'data/test.json')
        self.assertTrue(config.headless)
        self.assertEqual(config.timeout, 60)
        self.assertEqual(config.max_retries, 5)
    
    def test_scraping_config_invalid_extension(self):
        """Test ScrapingConfig with invalid file extension"""
        with self.assertRaises(ValidationError):
            ScrapingConfig(
                profile_url='https://linkedin.com/in/test',
                output_path='data/test.txt'  # Invalid extension
            )
    
    def test_scraping_config_delay_validation(self):
        """Test delay range validation in ScrapingConfig"""
        config = ScrapingConfig(
            profile_url='https://linkedin.com/in/test',
            delay_min=5.0,
            delay_max=2.0  # Should be corrected to >= delay_min
        )
        
        self.assertGreaterEqual(config.delay_max, config.delay_min)


class TestDataQualityAnalyzer(unittest.TestCase):
    """Test DataQualityAnalyzer functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.analyzer = DataQualityAnalyzer()
    
    def test_high_quality_profile(self):
        """Test analysis of high-quality profile data"""
        high_quality_data = {
            'url': 'https://linkedin.com/in/john-doe',
            'name': 'John Doe',
            'headline': 'Senior Software Engineer at Google with 8+ years of experience',
            'location': 'Mountain View, California, United States',
            'about': 'Passionate software engineer with extensive experience in building scalable web applications. Led multiple cross-functional teams and delivered high-impact products used by millions of users worldwide.',
            'experience': [
                'Senior Software Engineer at Google (2020-Present)',
                'Software Engineer at Facebook (2018-2020)',
                'Junior Developer at StartupXYZ (2016-2018)'
            ],
            'education': [
                'MS Computer Science - Stanford University (2014-2016)',
                'BS Computer Science - UC Berkeley (2010-2014)'
            ],
            'skills': ['Python', 'JavaScript', 'React', 'Node.js', 'AWS', 'Docker', 'Kubernetes'],
            'scraped_at': '2024-01-15 14:30:00'
        }
        
        report = self.analyzer.analyze_profile_quality(high_quality_data)
        
        self.assertIsInstance(report, QualityReport)
        self.assertGreater(report.overall_score, 0.8)
        self.assertGreater(report.completeness_score, 0.8)
        self.assertGreater(report.accuracy_score, 0.7)
        self.assertLess(len(report.issues), 3)  # Should have few issues
    
    def test_low_quality_profile(self):
        """Test analysis of low-quality profile data"""
        low_quality_data = {
            'url': 'https://linkedin.com/in/user',
            'name': 'User',
            'headline': '',
            'location': '',
            'about': '',
            'experience': [],
            'education': [],
            'skills': [],
            'scraped_at': '2024-01-15 14:30:00'
        }
        
        report = self.analyzer.analyze_profile_quality(low_quality_data)
        
        self.assertIsInstance(report, QualityReport)
        self.assertLess(report.overall_score, 0.4)
        self.assertLess(report.completeness_score, 0.3)
        self.assertGreater(len(report.issues), 5)  # Should have many issues
        self.assertGreater(len(report.suggestions), 2)
    
    def test_suspicious_content_detection(self):
        """Test detection of suspicious content"""
        suspicious_data = {
            'url': 'https://linkedin.com/in/test',
            'name': 'Test User 123',
            'headline': 'Lorem ipsum dolor sit amet',
            'location': 'Sample Location',
            'about': 'See more content by clicking here',
            'experience': ['Loading...', 'Failed to load'],
            'education': ['Example University'],
            'skills': ['test', 'sample'],
            'scraped_at': '2024-01-15 14:30:00'
        }
        
        report = self.analyzer.analyze_profile_quality(suspicious_data)
        
        # Should detect multiple suspicious patterns
        suspicious_issues = [
            issue for issue in report.issues 
            if issue.issue_type == IssueType.SUSPICIOUS_CONTENT
        ]
        self.assertGreater(len(suspicious_issues), 2)
    
    def test_missing_data_detection(self):
        """Test detection of missing data"""
        incomplete_data = {
            'url': 'https://linkedin.com/in/test',
            'name': 'John Doe',
            'headline': None,
            'location': '',
            'about': None,
            'experience': [],
            'education': None,
            'skills': [],
            'scraped_at': '2024-01-15 14:30:00'
        }
        
        report = self.analyzer.analyze_profile_quality(incomplete_data)
        
        # Should detect missing data issues
        missing_issues = [
            issue for issue in report.issues 
            if issue.issue_type == IssueType.MISSING_DATA
        ]
        self.assertGreater(len(missing_issues), 3)
    
    def test_invalid_format_detection(self):
        """Test detection of invalid formats"""
        invalid_format_data = {
            'url': 'https://linkedin.com/in/test',
            'name': 'A',  # Too short
            'headline': 'X' * 300,  # Too long
            'location': '123!@#$%',  # Invalid characters
            'about': 'Short',  # Too short for about section
            'experience': ['X'],  # Too short
            'education': ['Y'],  # Too short
            'skills': ['A' * 150],  # Too long for skill
            'scraped_at': '2024-01-15 14:30:00'
        }
        
        report = self.analyzer.analyze_profile_quality(invalid_format_data)
        
        # Should detect format issues
        format_issues = [
            issue for issue in report.issues 
            if issue.issue_type == IssueType.INVALID_FORMAT
        ]
        self.assertGreater(len(format_issues), 2)
    
    def test_duplicate_data_detection(self):
        """Test detection of duplicate data"""
        duplicate_data = {
            'url': 'https://linkedin.com/in/test',
            'name': 'John Doe',
            'headline': 'Software Engineer',
            'location': 'San Francisco',
            'about': 'Software engineer with experience...',
            'experience': ['Job 1', 'Job 2', 'Job 1', 'Job 3'],  # Duplicate
            'education': ['School A', 'School B', 'School A'],  # Duplicate
            'skills': ['Python', 'JavaScript', 'python', 'PYTHON'],  # Case duplicates
            'scraped_at': '2024-01-15 14:30:00'
        }
        
        report = self.analyzer.analyze_profile_quality(duplicate_data)
        
        # Should detect duplicate issues
        duplicate_issues = [
            issue for issue in report.issues 
            if issue.issue_type == IssueType.DUPLICATE_DATA
        ]
        self.assertGreater(len(duplicate_issues), 0)
    
    def test_field_scoring(self):
        """Test individual field scoring"""
        test_data = {
            'url': 'https://linkedin.com/in/test',
            'name': 'John Doe',
            'headline': 'Senior Software Engineer with 5+ years of experience',
            'location': 'San Francisco, CA',
            'about': 'Experienced software engineer...',
            'experience': ['Job 1', 'Job 2'],
            'education': ['School 1'],
            'skills': ['Python', 'JavaScript', 'React'],
            'scraped_at': '2024-01-15 14:30:00'
        }
        
        report = self.analyzer.analyze_profile_quality(test_data)
        
        self.assertIn('name', report.field_scores)
        self.assertIn('headline', report.field_scores)
        self.assertIn('location', report.field_scores)
        
        # Name should have high score (complete and valid)
        self.assertGreater(report.field_scores['name'], 0.8)
    
    def test_suggestions_generation(self):
        """Test quality improvement suggestions"""
        problematic_data = {
            'url': 'https://linkedin.com/in/test',
            'name': 'User',
            'headline': 'Loading...',
            'location': '',
            'about': 'See more',
            'experience': [],
            'education': [],
            'skills': ['test'],
            'scraped_at': '2024-01-15 14:30:00'
        }
        
        report = self.analyzer.analyze_profile_quality(problematic_data)
        
        self.assertGreater(len(report.suggestions), 2)
        self.assertIsInstance(report.suggestions[0], str)
        
        # Should suggest improvements for missing data and suspicious content
        suggestions_text = ' '.join(report.suggestions).lower()
        self.assertTrue(
            any(keyword in suggestions_text for keyword in ['missing', 'extraction', 'improve'])
        )


class TestDataQualityIntegration(unittest.TestCase):
    """Test integration between models and quality analysis"""
    
    def test_pydantic_with_quality_analysis(self):
        """Test Pydantic model integration with quality analysis"""
        raw_data = {
            'url': 'linkedin.com/in/test-user',
            'name': '  John   Doe  ',
            'headline': 'Software Engineer at Tech Corp',
            'location': 'San Francisco, CA',
            'about': 'Experienced developer...',
            'experience': ['Job 1', 'Job 2', 'job 1'],  # Has duplicate
            'education': ['School 1'],
            'skills': ['Python', 'python', 'JavaScript'],  # Has duplicate
            'scraped_at': '2024-01-15 14:30:00'
        }
        
        # Validate with Pydantic
        profile = ProfileData(**raw_data)
        
        # Analyze quality
        analyzer = DataQualityAnalyzer()
        report = analyzer.analyze_profile_quality(raw_data)
        
        # Profile should be created successfully
        self.assertEqual(profile.name, 'John Doe')  # Sanitized
        self.assertEqual(profile.url, 'https://linkedin.com/in/test-user/')  # Normalized
        
        # Quality analysis should detect issues
        self.assertIsInstance(report, QualityReport)
        self.assertGreater(report.overall_score, 0.5)  # Reasonable quality
        
        # Should detect duplicates
        duplicate_issues = [
            issue for issue in report.issues 
            if issue.issue_type == IssueType.DUPLICATE_DATA
        ]
        self.assertGreaterEqual(len(duplicate_issues), 1)


if __name__ == '__main__':
    print("🧪 Running Step 3 Tests: Data Validation and Sanitization")
    print("-" * 60)
    
    # Run tests with verbose output
    unittest.main(verbosity=2, exit=False)
    
    print("\n✅ Step 3 tests completed!")
    print("💡 These tests verify Pydantic models, data quality analysis, and advanced validation.") 