"""
Step 13: Analytics and Reporting
Data analysis, trends, and comprehensive reporting
"""

import json
from typing import Dict, List, Any
from collections import Counter
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class ScrapingAnalytics:
    """Analytics for scraped LinkedIn data"""
    
    def __init__(self):
        self.profiles_data = []
        self.scraping_sessions = []
    
    def add_profile(self, profile_data: Dict[str, Any]):
        """Add profile data for analysis"""
        self.profiles_data.append(profile_data)
    
    def get_skill_trends(self) -> Dict[str, int]:
        """Analyze skill trends across profiles"""
        all_skills = []
        for profile in self.profiles_data:
            skills = profile.get('skills', [])
            if isinstance(skills, list):
                all_skills.extend(skills)
        
        return dict(Counter(all_skills).most_common(20))
    
    def get_location_distribution(self) -> Dict[str, int]:
        """Analyze location distribution"""
        locations = []
        for profile in self.profiles_data:
            location = profile.get('location', '').strip()
            if location:
                # Extract city from location string
                city = location.split(',')[0].strip()
                locations.append(city)
        
        return dict(Counter(locations).most_common(10))
    
    def get_quality_statistics(self) -> Dict[str, float]:
        """Calculate quality score statistics"""
        quality_scores = []
        for profile in self.profiles_data:
            score = profile.get('quality_score')
            if score is not None:
                quality_scores.append(score)
        
        if not quality_scores:
            return {'count': 0, 'average': 0, 'min': 0, 'max': 0}
        
        return {
            'count': len(quality_scores),
            'average': sum(quality_scores) / len(quality_scores),
            'min': min(quality_scores),
            'max': max(quality_scores)
        }
    
    def get_company_insights(self) -> Dict[str, int]:
        """Analyze company distribution from headlines"""
        companies = []
        for profile in self.profiles_data:
            headline = profile.get('headline', '')
            # Simple extraction of company from headline
            if ' at ' in headline:
                company = headline.split(' at ')[-1].strip()
                companies.append(company)
        
        return dict(Counter(companies).most_common(15))
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive analytics report"""
        return {
            'overview': {
                'total_profiles': len(self.profiles_data),
                'generated_at': datetime.now().isoformat(),
                'data_quality': self.get_quality_statistics()
            },
            'skills_analysis': {
                'top_skills': self.get_skill_trends(),
                'total_unique_skills': len(set(skill for profile in self.profiles_data 
                                            for skill in profile.get('skills', [])))
            },
            'geographic_distribution': self.get_location_distribution(),
            'company_insights': self.get_company_insights(),
            'profile_completeness': self._analyze_completeness()
        }
    
    def _analyze_completeness(self) -> Dict[str, Any]:
        """Analyze profile data completeness"""
        fields = ['name', 'headline', 'location', 'about', 'experience', 'education', 'skills']
        completeness_stats = {}
        
        for field in fields:
            filled_count = 0
            for profile in self.profiles_data:
                value = profile.get(field)
                if value:
                    if isinstance(value, list) and len(value) > 0:
                        filled_count += 1
                    elif isinstance(value, str) and value.strip():
                        filled_count += 1
            
            completeness_stats[field] = {
                'filled': filled_count,
                'percentage': (filled_count / len(self.profiles_data) * 100) if self.profiles_data else 0
            }
        
        return completeness_stats
    
    def save_report(self, filepath: str):
        """Save analytics report to file"""
        try:
            report = self.generate_report()
            with open(filepath, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            logger.info(f"Analytics report saved to {filepath}")
        except Exception as e:
            logger.error(f"Failed to save analytics report: {e}")

# Global analytics instance
analytics = ScrapingAnalytics() 