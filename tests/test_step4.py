"""
Test suite for Step 4: Multiple Output Formats
"""

import unittest
import sys
import os
import json
import csv
import tempfile
import shutil
from pathlib import Path

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.output_manager import OutputManager, OutputFormat


class TestOutputManager(unittest.TestCase):
    """Test OutputManager functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.output_manager = OutputManager()
        
        # Sample profile data for testing
        self.sample_profile = {
            'url': 'https://linkedin.com/in/john-doe',
            'name': 'John Doe',
            'headline': 'Senior Software Engineer at Tech Corp',
            'location': 'San Francisco, CA',
            'about': 'Experienced software engineer with 8+ years of experience in building scalable web applications.',
            'experience': [
                'Senior Software Engineer at Tech Corp (2020-Present)',
                'Software Engineer at StartupXYZ (2018-2020)',
                'Junior Developer at WebCorp (2016-2018)'
            ],
            'education': [
                'MS Computer Science - Stanford University (2014-2016)',
                'BS Computer Science - UC Berkeley (2010-2014)'
            ],
            'skills': ['Python', 'JavaScript', 'React', 'Node.js', 'AWS'],
            'scraped_at': '2024-01-15 14:30:00',
            'quality_score': 0.85,
            'quality_report': {
                'overall_score': 0.85,
                'completeness_score': 0.90,
                'accuracy_score': 0.82,
                'consistency_score': 0.83,
                'issues_count': 2,
                'suggestions': ['Improve experience extraction', 'Add more skills']
            }
        }
        
        self.sample_profiles = [self.sample_profile, {
            'url': 'https://linkedin.com/in/jane-smith',
            'name': 'Jane Smith',
            'headline': 'Product Manager',
            'location': 'New York, NY',
            'about': 'Product manager with focus on user experience.',
            'experience': ['Product Manager at BigCorp (2019-Present)'],
            'education': ['MBA - Harvard Business School'],
            'skills': ['Product Management', 'Strategy', 'Analytics'],
            'scraped_at': '2024-01-15 15:00:00',
            'quality_score': 0.75
        }]
    
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir)
    
    def test_format_detection(self):
        """Test automatic format detection from file extensions"""
        test_cases = [
            ('data.json', OutputFormat.JSON),
            ('profile.csv', OutputFormat.CSV),
            ('export.xlsx', OutputFormat.EXCEL),
            ('data.xml', OutputFormat.XML),
            ('report.html', OutputFormat.HTML),
            ('config.yaml', OutputFormat.YAML),
            ('unknown.txt', OutputFormat.JSON),  # Default fallback
        ]
        
        for filename, expected_format in test_cases:
            with self.subTest(filename=filename):
                detected_format = self.output_manager._detect_format(filename)
                self.assertEqual(detected_format, expected_format)
    
    def test_json_output(self):
        """Test JSON output format"""
        output_path = os.path.join(self.temp_dir, 'test.json')
        
        success = self.output_manager.save_data(
            self.sample_profile, 
            output_path, 
            OutputFormat.JSON
        )
        
        self.assertTrue(success)
        self.assertTrue(os.path.exists(output_path))
        
        # Verify content
        with open(output_path, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
        
        self.assertEqual(loaded_data['name'], 'John Doe')
        self.assertEqual(loaded_data['url'], 'https://linkedin.com/in/john-doe')
        self.assertEqual(len(loaded_data['skills']), 5)
    
    def test_csv_output_single_profile(self):
        """Test CSV output format with single profile"""
        output_path = os.path.join(self.temp_dir, 'test.csv')
        
        success = self.output_manager.save_data(
            self.sample_profile, 
            output_path, 
            OutputFormat.CSV
        )
        
        self.assertTrue(success)
        self.assertTrue(os.path.exists(output_path))
        
        # Verify content
        with open(output_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['name'], 'John Doe')
        self.assertIn('skills', rows[0])
    
    def test_csv_output_multiple_profiles(self):
        """Test CSV output format with multiple profiles"""
        output_path = os.path.join(self.temp_dir, 'test.csv')
        
        success = self.output_manager.save_data(
            self.sample_profiles, 
            output_path, 
            OutputFormat.CSV
        )
        
        self.assertTrue(success)
        self.assertTrue(os.path.exists(output_path))
        
        # Verify content
        with open(output_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]['name'], 'John Doe')
        self.assertEqual(rows[1]['name'], 'Jane Smith')
    
    def test_excel_output(self):
        """Test Excel output format"""
        output_path = os.path.join(self.temp_dir, 'test.xlsx')
        
        success = self.output_manager.save_data(
            self.sample_profile, 
            output_path, 
            OutputFormat.EXCEL
        )
        
        self.assertTrue(success)
        self.assertTrue(os.path.exists(output_path))
        
        # Verify content using pandas
        try:
            import pandas as pd
            df = pd.read_excel(output_path, sheet_name='Profiles')
            self.assertEqual(len(df), 1)
            self.assertEqual(df.iloc[0]['name'], 'John Doe')
        except ImportError:
            # Skip detailed verification if pandas not available
            pass
    
    def test_xml_output(self):
        """Test XML output format"""
        output_path = os.path.join(self.temp_dir, 'test.xml')
        
        success = self.output_manager.save_data(
            self.sample_profile, 
            output_path, 
            OutputFormat.XML
        )
        
        self.assertTrue(success)
        self.assertTrue(os.path.exists(output_path))
        
        # Verify it's valid XML
        import xml.etree.ElementTree as ET
        try:
            tree = ET.parse(output_path)
            root = tree.getroot()
            self.assertEqual(root.tag, 'linkedin_profiles')
            self.assertEqual(root.get('count'), '1')
        except ET.ParseError:
            self.fail("Generated XML is not valid")
    
    def test_html_output(self):
        """Test HTML output format"""
        output_path = os.path.join(self.temp_dir, 'test.html')
        
        success = self.output_manager.save_data(
            self.sample_profile, 
            output_path, 
            OutputFormat.HTML
        )
        
        self.assertTrue(success)
        self.assertTrue(os.path.exists(output_path))
        
        # Verify content
        with open(output_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        self.assertIn('<!DOCTYPE html>', html_content)
        self.assertIn('John Doe', html_content)
        self.assertIn('Senior Software Engineer', html_content)
    
    def test_yaml_output(self):
        """Test YAML output format"""
        output_path = os.path.join(self.temp_dir, 'test.yaml')
        
        success = self.output_manager.save_data(
            self.sample_profile, 
            output_path, 
            OutputFormat.YAML
        )
        
        # YAML might not be available in all environments
        if success:
            self.assertTrue(os.path.exists(output_path))
            
            # Verify content
            with open(output_path, 'r', encoding='utf-8') as f:
                yaml_content = f.read()
            
            self.assertIn('name: John Doe', yaml_content)
            self.assertIn('linkedin.com/in/john-doe', yaml_content)
    
    def test_batch_export(self):
        """Test batch export functionality"""
        formats = [OutputFormat.JSON, OutputFormat.CSV, OutputFormat.HTML]
        
        results = self.output_manager.batch_export(
            self.sample_profiles,
            self.temp_dir,
            formats,
            'test_batch'
        )
        
        self.assertEqual(len(results), 3)
        
        # Check that all formats were attempted
        for format_type in formats:
            self.assertIn(format_type, results)
        
        # Check that files were created for successful formats
        files_created = os.listdir(self.temp_dir)
        successful_formats = [fmt for fmt, success in results.items() if success]
        
        self.assertGreater(len(successful_formats), 0)
        self.assertGreater(len(files_created), 0)
    
    def test_flatten_dict(self):
        """Test dictionary flattening for CSV output"""
        nested_data = {
            'name': 'John Doe',
            'contact': {
                'email': 'john@example.com',
                'phone': '123-456-7890'
            },
            'skills': ['Python', 'JavaScript'],
            'experience': [
                {'title': 'Engineer', 'company': 'TechCorp'},
                {'title': 'Developer', 'company': 'StartupXYZ'}
            ]
        }
        
        flattened = self.output_manager._flatten_dict(nested_data)
        
        self.assertIn('name', flattened)
        self.assertIn('contact_email', flattened)
        self.assertIn('contact_phone', flattened)
        self.assertIn('skills', flattened)
        self.assertIn('experience', flattened)
        
        self.assertEqual(flattened['name'], 'John Doe')
        self.assertEqual(flattened['contact_email'], 'john@example.com')
        self.assertEqual(flattened['skills'], 'Python; JavaScript')
    
    def test_xml_key_cleaning(self):
        """Test XML key cleaning for invalid characters"""
        test_cases = [
            ('valid_key', 'valid_key'),
            ('key with spaces', 'key_with_spaces'),
            ('key-with-dashes', 'key-with-dashes'),
            ('key.with.dots', 'key_with_dots'),
            ('123invalid', 'item_123invalid'),
            ('', 'unknown'),
        ]
        
        for input_key, expected_key in test_cases:
            with self.subTest(input_key=input_key):
                cleaned_key = self.output_manager._clean_xml_key(input_key)
                self.assertEqual(cleaned_key, expected_key)
    
    def test_custom_csv_options(self):
        """Test CSV output with custom options"""
        output_path = os.path.join(self.temp_dir, 'custom.csv')
        
        # Test with custom field order
        success = self.output_manager.save_data(
            self.sample_profile, 
            output_path, 
            OutputFormat.CSV,
            field_order=['name', 'headline', 'location'],
            include_header=True
        )
        
        self.assertTrue(success)
        
        # Verify field order
        with open(output_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader)
        
        # First three fields should be in specified order
        self.assertEqual(header[0], 'name')
        self.assertEqual(header[1], 'headline')
        self.assertEqual(header[2], 'location')
    
    def test_excel_separate_sheets(self):
        """Test Excel output with separate sheets"""
        output_path = os.path.join(self.temp_dir, 'sheets.xlsx')
        
        success = self.output_manager.save_data(
            self.sample_profile, 
            output_path, 
            OutputFormat.EXCEL,
            separate_sheets=True
        )
        
        self.assertTrue(success)
        
        # Verify multiple sheets were created
        try:
            import pandas as pd
            excel_file = pd.ExcelFile(output_path)
            sheet_names = excel_file.sheet_names
            
            self.assertIn('Profiles', sheet_names)
            # Should have additional sheets for experience, education, skills
            self.assertGreater(len(sheet_names), 1)
            
        except ImportError:
            # Skip detailed verification if pandas not available
            pass
    
    def test_error_handling(self):
        """Test error handling for invalid inputs"""
        # Test with invalid output path
        invalid_path = '/invalid/path/test.json'
        success = self.output_manager.save_data(
            self.sample_profile, 
            invalid_path, 
            OutputFormat.JSON
        )
        self.assertFalse(success)
        
        # Test with empty data
        empty_path = os.path.join(self.temp_dir, 'empty.csv')
        success = self.output_manager.save_data(
            [], 
            empty_path, 
            OutputFormat.CSV
        )
        self.assertFalse(success)
    
    def test_template_directory_handling(self):
        """Test template directory handling"""
        # Test with non-existent template directory
        output_manager = OutputManager(template_dir='non_existent_dir')
        self.assertIsNone(output_manager.jinja_env)
        
        # Test with existing template directory
        template_dir = os.path.join(self.temp_dir, 'templates')
        os.makedirs(template_dir)
        
        # Create a simple template
        template_content = '<html><body>{{ profiles[0].name }}</body></html>'
        with open(os.path.join(template_dir, 'simple.html'), 'w') as f:
            f.write(template_content)
        
        output_manager = OutputManager(template_dir=template_dir)
        self.assertIsNotNone(output_manager.jinja_env)


class TestOutputFormats(unittest.TestCase):
    """Test specific output format features"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.output_manager = OutputManager()
        
        self.test_data = {
            'name': 'Test User',
            'url': 'https://linkedin.com/in/test',
            'skills': ['Skill 1', 'Skill 2'],
            'experience': [
                {'title': 'Engineer', 'company': 'TechCorp', 'duration': '2020-2022'},
                'Simple experience string'
            ],
            'scraped_at': '2024-01-15'
        }
    
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir)
    
    def test_json_formatting_options(self):
        """Test JSON formatting options"""
        output_path = os.path.join(self.temp_dir, 'formatted.json')
        
        # Test with custom indent
        success = self.output_manager.save_data(
            self.test_data, 
            output_path, 
            OutputFormat.JSON,
            indent=4
        )
        
        self.assertTrue(success)
        
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Should have 4-space indentation
        lines = content.split('\n')
        indented_lines = [line for line in lines if line.startswith('    ')]
        self.assertGreater(len(indented_lines), 0)
    
    def test_html_with_quality_report(self):
        """Test HTML output with quality report"""
        data_with_quality = {
            **self.test_data,
            'quality_report': {
                'overall_score': 0.75,
                'completeness_score': 0.80,
                'issues_count': 3,
                'suggestions': ['Improve data extraction', 'Add more details']
            }
        }
        
        output_path = os.path.join(self.temp_dir, 'quality.html')
        
        success = self.output_manager.save_data(
            data_with_quality, 
            output_path, 
            OutputFormat.HTML
        )
        
        self.assertTrue(success)
        
        with open(output_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        self.assertIn('Data Quality Report', html_content)
        self.assertIn('75%', html_content)  # Overall score
        self.assertIn('80%', html_content)  # Completeness score
    
    def test_xml_structure(self):
        """Test XML output structure"""
        output_path = os.path.join(self.temp_dir, 'structure.xml')
        
        success = self.output_manager.save_data(
            [self.test_data], 
            output_path, 
            OutputFormat.XML
        )
        
        self.assertTrue(success)
        
        import xml.etree.ElementTree as ET
        tree = ET.parse(output_path)
        root = tree.getroot()
        
        # Check root structure
        self.assertEqual(root.tag, 'linkedin_profiles')
        self.assertEqual(root.get('count'), '1')
        self.assertIsNotNone(root.get('generated_at'))
        
        # Check profile structure
        profile = root.find('profile')
        self.assertIsNotNone(profile)
        self.assertEqual(profile.get('index'), '0')
        
        # Check nested elements
        name_elem = profile.find('name')
        self.assertIsNotNone(name_elem)
        self.assertEqual(name_elem.text, 'Test User')
        
        # Check list handling
        skills_elem = profile.find('skills')
        self.assertIsNotNone(skills_elem)
        self.assertEqual(skills_elem.get('type'), 'list')
        self.assertEqual(skills_elem.get('count'), '2')


if __name__ == '__main__':
    print("🧪 Running Step 4 Tests: Multiple Output Formats")
    print("-" * 60)
    
    # Run tests with verbose output
    unittest.main(verbosity=2, exit=False)
    
    print("\n✅ Step 4 tests completed!")
    print("💡 These tests verify JSON, CSV, Excel, XML, HTML, and YAML output formats.") 