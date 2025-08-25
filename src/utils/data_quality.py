"""
Step 3: Advanced Data Quality Analysis
Comprehensive data quality assessment and improvement suggestions
"""

import re
import logging
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class IssueType(str, Enum):
    """Types of data quality issues"""
    MISSING_DATA = "missing_data"
    INVALID_FORMAT = "invalid_format"
    SUSPICIOUS_CONTENT = "suspicious_content"
    INCOMPLETE_EXTRACTION = "incomplete_extraction"
    DUPLICATE_DATA = "duplicate_data"
    ENCODING_ISSUE = "encoding_issue"


class Severity(str, Enum):
    """Issue severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class QualityIssue:
    """Data quality issue representation"""
    issue_type: IssueType
    severity: Severity
    field: str
    message: str
    suggestion: Optional[str] = None
    value: Optional[str] = None


@dataclass
class QualityReport:
    """Comprehensive data quality report"""
    overall_score: float
    completeness_score: float
    accuracy_score: float
    consistency_score: float
    issues: List[QualityIssue]
    suggestions: List[str]
    field_scores: Dict[str, float]


class DataQualityAnalyzer:
    """Advanced data quality analysis for LinkedIn profile data"""
    
    # Patterns for detecting suspicious content
    SUSPICIOUS_PATTERNS = {
        'generic_placeholder': [
            r'^(name|user|person|individual)(\s*\d+)?$',
            r'^(test|sample|example|demo)(\s*\w+)*$',
            r'^(lorem\s+ipsum|placeholder|dummy\s+text)',
        ],
        'encoding_issues': [
            r'[^\x00-\x7F]+',  # Non-ASCII characters that might be encoding issues
            r'â€™|â€œ|â€\x9d',  # Common encoding artifacts
        ],
        'extraction_errors': [
            r'^\s*(see\s+more|show\s+more|read\s+more)\s*$',
            r'^\s*(click\s+to\s+expand|view\s+full\s+profile)\s*$',
            r'^\s*(loading|error|failed\s+to\s+load)\s*$',
        ],
        'incomplete_sentences': [
            r'^[a-z]',  # Starts with lowercase (might be truncated)
            r'[^.!?]$',  # Doesn't end with punctuation
        ]
    }
    
    # Expected formats for different fields
    FIELD_FORMATS = {
        'name': {
            'min_length': 2,
            'max_length': 100,
            'pattern': r'^[a-zA-Z\s\-\'\.]+$',
            'required_words': 1
        },
        'headline': {
            'min_length': 5,
            'max_length': 220,
            'pattern': None,
            'required_words': 2
        },
        'location': {
            'min_length': 2,
            'max_length': 100,
            'pattern': r'^[a-zA-Z\s\-\,\.]+$',
            'required_words': 1
        },
        'about': {
            'min_length': 10,
            'max_length': 2600,
            'pattern': None,
            'required_words': 5
        }
    }
    
    def analyze_profile_quality(self, profile_data: Dict[str, Any]) -> QualityReport:
        """
        Perform comprehensive quality analysis on profile data
        
        Args:
            profile_data: Dictionary containing profile data
            
        Returns:
            QualityReport with detailed analysis
        """
        issues = []
        field_scores = {}
        suggestions = []
        
        # Analyze each field
        for field, value in profile_data.items():
            if field in ['scraped_at', 'url', 'quality_score']:
                continue
                
            field_issues, field_score = self._analyze_field(field, value)
            issues.extend(field_issues)
            field_scores[field] = field_score
        
        # Calculate overall scores
        completeness_score = self._calculate_completeness_score(profile_data)
        accuracy_score = self._calculate_accuracy_score(field_scores)
        consistency_score = self._calculate_consistency_score(profile_data, issues)
        overall_score = (completeness_score * 0.4 + accuracy_score * 0.4 + consistency_score * 0.2)
        
        # Generate suggestions
        suggestions = self._generate_suggestions(issues, profile_data)
        
        return QualityReport(
            overall_score=overall_score,
            completeness_score=completeness_score,
            accuracy_score=accuracy_score,
            consistency_score=consistency_score,
            issues=issues,
            suggestions=suggestions,
            field_scores=field_scores
        )
    
    def _analyze_field(self, field_name: str, value: Any) -> Tuple[List[QualityIssue], float]:
        """Analyze individual field quality"""
        issues = []
        score = 1.0
        
        # Handle None or empty values
        if value is None or (isinstance(value, str) and not value.strip()):
            if field_name in ['name']:  # Required fields
                issues.append(QualityIssue(
                    issue_type=IssueType.MISSING_DATA,
                    severity=Severity.CRITICAL,
                    field=field_name,
                    message=f"Required field '{field_name}' is missing",
                    suggestion=f"Ensure {field_name} extraction is working correctly"
                ))
                return issues, 0.0
            else:
                issues.append(QualityIssue(
                    issue_type=IssueType.MISSING_DATA,
                    severity=Severity.MEDIUM,
                    field=field_name,
                    message=f"Optional field '{field_name}' is empty",
                    suggestion=f"Consider improving {field_name} extraction"
                ))
                return issues, 0.3
        
        # Handle list fields
        if isinstance(value, list):
            return self._analyze_list_field(field_name, value)
        
        # Handle string fields
        if isinstance(value, str):
            return self._analyze_string_field(field_name, value)
        
        return issues, score
    
    def _analyze_string_field(self, field_name: str, value: str) -> Tuple[List[QualityIssue], float]:
        """Analyze string field quality"""
        issues = []
        score = 1.0
        
        # Get field format requirements
        format_req = self.FIELD_FORMATS.get(field_name, {})
        
        # Check length
        min_len = format_req.get('min_length', 1)
        max_len = format_req.get('max_length', 1000)
        
        if len(value) < min_len:
            issues.append(QualityIssue(
                issue_type=IssueType.INVALID_FORMAT,
                severity=Severity.HIGH,
                field=field_name,
                message=f"Field '{field_name}' is too short ({len(value)} < {min_len})",
                value=value[:50],
                suggestion=f"Verify {field_name} extraction is complete"
            ))
            score *= 0.5
        
        if len(value) > max_len:
            issues.append(QualityIssue(
                issue_type=IssueType.INVALID_FORMAT,
                severity=Severity.MEDIUM,
                field=field_name,
                message=f"Field '{field_name}' is too long ({len(value)} > {max_len})",
                value=value[:50] + "...",
                suggestion=f"Consider truncating {field_name} content"
            ))
            score *= 0.8
        
        # Check pattern
        pattern = format_req.get('pattern')
        if pattern and not re.match(pattern, value, re.IGNORECASE):
            issues.append(QualityIssue(
                issue_type=IssueType.INVALID_FORMAT,
                severity=Severity.MEDIUM,
                field=field_name,
                message=f"Field '{field_name}' doesn't match expected format",
                value=value[:50],
                suggestion=f"Review {field_name} format validation"
            ))
            score *= 0.7
        
        # Check for suspicious patterns
        for pattern_type, patterns in self.SUSPICIOUS_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, value, re.IGNORECASE):
                    severity = Severity.HIGH if pattern_type == 'extraction_errors' else Severity.MEDIUM
                    issues.append(QualityIssue(
                        issue_type=IssueType.SUSPICIOUS_CONTENT,
                        severity=severity,
                        field=field_name,
                        message=f"Suspicious content detected: {pattern_type}",
                        value=value[:50],
                        suggestion=f"Review {field_name} extraction logic"
                    ))
                    score *= 0.6 if severity == Severity.HIGH else 0.8
        
        # Check word count
        required_words = format_req.get('required_words', 1)
        word_count = len(value.split())
        if word_count < required_words:
            issues.append(QualityIssue(
                issue_type=IssueType.INCOMPLETE_EXTRACTION,
                severity=Severity.MEDIUM,
                field=field_name,
                message=f"Field '{field_name}' has too few words ({word_count} < {required_words})",
                value=value[:50],
                suggestion=f"Verify {field_name} extraction completeness"
            ))
            score *= 0.8
        
        return issues, max(score, 0.0)
    
    def _analyze_list_field(self, field_name: str, value: List[Any]) -> Tuple[List[QualityIssue], float]:
        """Analyze list field quality"""
        issues = []
        score = 1.0
        
        if not value:
            issues.append(QualityIssue(
                issue_type=IssueType.MISSING_DATA,
                severity=Severity.MEDIUM,
                field=field_name,
                message=f"List field '{field_name}' is empty",
                suggestion=f"Improve {field_name} extraction to capture more items"
            ))
            return issues, 0.2
        
        # Check for duplicates
        if isinstance(value[0], str):
            unique_items = set(str(item).lower().strip() for item in value)
            if len(unique_items) < len(value):
                issues.append(QualityIssue(
                    issue_type=IssueType.DUPLICATE_DATA,
                    severity=Severity.LOW,
                    field=field_name,
                    message=f"Field '{field_name}' contains duplicate items",
                    suggestion=f"Remove duplicates from {field_name}"
                ))
                score *= 0.9
        
        # Analyze individual items
        item_scores = []
        for i, item in enumerate(value[:10]):  # Limit to first 10 items
            if isinstance(item, str):
                item_issues, item_score = self._analyze_string_field(f"{field_name}[{i}]", item)
                issues.extend(item_issues)
                item_scores.append(item_score)
        
        if item_scores:
            avg_item_score = sum(item_scores) / len(item_scores)
            score *= avg_item_score
        
        # Expected minimum items
        min_items = {'experience': 1, 'education': 1, 'skills': 3}.get(field_name, 1)
        if len(value) < min_items:
            issues.append(QualityIssue(
                issue_type=IssueType.INCOMPLETE_EXTRACTION,
                severity=Severity.MEDIUM,
                field=field_name,
                message=f"Field '{field_name}' has fewer items than expected ({len(value)} < {min_items})",
                suggestion=f"Improve {field_name} extraction to capture more items"
            ))
            score *= 0.7
        
        return issues, max(score, 0.0)
    
    def _calculate_completeness_score(self, profile_data: Dict[str, Any]) -> float:
        """Calculate data completeness score"""
        total_fields = 7  # name, headline, location, about, experience, education, skills
        filled_fields = 0
        
        required_fields = ['name']
        optional_fields = ['headline', 'location', 'about']
        list_fields = ['experience', 'education', 'skills']
        
        # Required fields
        for field in required_fields:
            if field in profile_data and profile_data[field]:
                filled_fields += 1
        
        # Optional fields
        for field in optional_fields:
            if field in profile_data and profile_data[field] and str(profile_data[field]).strip():
                filled_fields += 1
        
        # List fields
        for field in list_fields:
            if field in profile_data and isinstance(profile_data[field], list) and len(profile_data[field]) > 0:
                filled_fields += 1
        
        return filled_fields / total_fields
    
    def _calculate_accuracy_score(self, field_scores: Dict[str, float]) -> float:
        """Calculate data accuracy score based on field scores"""
        if not field_scores:
            return 0.0
        
        # Weight different fields
        weights = {
            'name': 0.25,
            'headline': 0.20,
            'location': 0.10,
            'about': 0.15,
            'experience': 0.15,
            'education': 0.10,
            'skills': 0.05
        }
        
        weighted_score = 0.0
        total_weight = 0.0
        
        for field, score in field_scores.items():
            weight = weights.get(field, 0.05)
            weighted_score += score * weight
            total_weight += weight
        
        return weighted_score / total_weight if total_weight > 0 else 0.0
    
    def _calculate_consistency_score(self, profile_data: Dict[str, Any], issues: List[QualityIssue]) -> float:
        """Calculate data consistency score"""
        # Start with perfect score
        score = 1.0
        
        # Penalize for critical and high severity issues
        for issue in issues:
            if issue.severity == Severity.CRITICAL:
                score *= 0.5
            elif issue.severity == Severity.HIGH:
                score *= 0.8
            elif issue.severity == Severity.MEDIUM:
                score *= 0.9
        
        # Check for consistency between fields
        name = profile_data.get('name', '')
        headline = profile_data.get('headline', '')
        
        # If name appears to be a placeholder but headline is detailed
        if name and headline:
            if (len(name.split()) == 1 and len(name) < 10 and 
                len(headline) > 50 and len(headline.split()) > 5):
                score *= 0.8  # Possible name extraction issue
        
        return max(score, 0.0)
    
    def _generate_suggestions(self, issues: List[QualityIssue], profile_data: Dict[str, Any]) -> List[str]:
        """Generate improvement suggestions based on issues"""
        suggestions = []
        
        # Group issues by type
        issue_types = {}
        for issue in issues:
            if issue.issue_type not in issue_types:
                issue_types[issue.issue_type] = []
            issue_types[issue.issue_type].append(issue)
        
        # Generate suggestions based on issue patterns
        if IssueType.MISSING_DATA in issue_types:
            missing_fields = [issue.field for issue in issue_types[IssueType.MISSING_DATA]]
            suggestions.append(f"Improve extraction for missing fields: {', '.join(set(missing_fields))}")
        
        if IssueType.SUSPICIOUS_CONTENT in issue_types:
            suspicious_fields = [issue.field for issue in issue_types[IssueType.SUSPICIOUS_CONTENT]]
            suggestions.append(f"Review extraction logic for fields with suspicious content: {', '.join(set(suspicious_fields))}")
        
        if IssueType.INCOMPLETE_EXTRACTION in issue_types:
            suggestions.append("Consider using more robust selectors or waiting longer for page content to load")
        
        if IssueType.INVALID_FORMAT in issue_types:
            suggestions.append("Add format validation and sanitization for extracted data")
        
        # Overall suggestions based on completeness
        completeness = len([f for f in ['headline', 'location', 'about', 'experience', 'education', 'skills'] 
                          if profile_data.get(f)])
        if completeness < 4:
            suggestions.append("Profile appears incomplete - consider checking page load timing or selectors")
        
        return suggestions[:5]  # Limit to top 5 suggestions 