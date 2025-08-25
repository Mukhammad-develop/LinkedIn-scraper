"""
Step 12: Advanced Search Capabilities
LinkedIn profile search by name, company, skills, location
"""

import re
from typing import List, Dict, Any, Optional
from urllib.parse import quote
import logging

logger = logging.getLogger(__name__)

class LinkedInSearchEngine:
    """Advanced LinkedIn search functionality"""
    
    def __init__(self):
        self.base_search_url = "https://www.linkedin.com/search/results/people/"
    
    def build_search_url(self, 
                        name: Optional[str] = None,
                        company: Optional[str] = None,
                        location: Optional[str] = None,
                        skills: List[str] = None,
                        title: Optional[str] = None) -> str:
        """Build LinkedIn search URL with filters"""
        
        params = []
        
        if name:
            params.append(f"keywords={quote(name)}")
        
        if company:
            params.append(f"currentCompany=[{quote(company)}]")
        
        if location:
            params.append(f"geoUrn=[{quote(location)}]")
        
        if title:
            params.append(f"title={quote(title)}")
        
        if skills:
            skills_param = ",".join([quote(skill) for skill in skills])
            params.append(f"skillExperience=[{skills_param}]")
        
        if params:
            return f"{self.base_search_url}?{'&'.join(params)}"
        
        return self.base_search_url
    
    def extract_profile_urls(self, search_results_html: str) -> List[str]:
        """Extract profile URLs from search results HTML"""
        profile_urls = []
        
        # Pattern to match LinkedIn profile URLs
        pattern = r'href="(/in/[^"]+)"'
        matches = re.findall(pattern, search_results_html)
        
        for match in matches:
            full_url = f"https://www.linkedin.com{match}"
            if full_url not in profile_urls:
                profile_urls.append(full_url)
        
        return profile_urls[:20]  # Limit to first 20 results
    
    def search_profiles(self, search_criteria: Dict[str, Any]) -> Dict[str, Any]:
        """Search for profiles based on criteria"""
        search_url = self.build_search_url(**search_criteria)
        
        return {
            'search_url': search_url,
            'criteria': search_criteria,
            'estimated_results': 'Unknown (requires scraping)',
            'filters_applied': len([v for v in search_criteria.values() if v])
        }

# Global search engine instance
search_engine = LinkedInSearchEngine() 