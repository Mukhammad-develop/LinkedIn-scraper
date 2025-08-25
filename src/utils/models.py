"""
Step 3: Pydantic Models for Data Validation
Advanced data validation with schema enforcement
"""

from datetime import datetime
from typing import List, Optional, Union
from pydantic import BaseModel, Field, validator, root_validator
from enum import Enum


class DataQuality(str, Enum):
    """Data quality levels"""
    EXCELLENT = "excellent"  # 0.8-1.0
    GOOD = "good"           # 0.6-0.8
    FAIR = "fair"           # 0.4-0.6
    POOR = "poor"           # 0.0-0.4


class ExperienceEntry(BaseModel):
    """Individual experience entry model"""
    title: Optional[str] = Field(None, max_length=200)
    company: Optional[str] = Field(None, max_length=200)
    duration: Optional[str] = Field(None, max_length=100)
    location: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=2000)
    raw_text: str = Field(..., min_length=1, max_length=1000)

    @validator('title', 'company', 'duration', 'location', pre=True)
    def sanitize_text_fields(cls, v):
        if isinstance(v, str):
            return ' '.join(v.split()).strip()
        return v

    @validator('raw_text', pre=True)
    def validate_raw_text(cls, v):
        if not v or not isinstance(v, str):
            raise ValueError("Raw text is required")
        return ' '.join(str(v).split()).strip()


class EducationEntry(BaseModel):
    """Individual education entry model"""
    institution: Optional[str] = Field(None, max_length=200)
    degree: Optional[str] = Field(None, max_length=200)
    field_of_study: Optional[str] = Field(None, max_length=200)
    duration: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    raw_text: str = Field(..., min_length=1, max_length=1000)

    @validator('institution', 'degree', 'field_of_study', 'duration', pre=True)
    def sanitize_text_fields(cls, v):
        if isinstance(v, str):
            return ' '.join(v.split()).strip()
        return v

    @validator('raw_text', pre=True)
    def validate_raw_text(cls, v):
        if not v or not isinstance(v, str):
            raise ValueError("Raw text is required")
        return ' '.join(str(v).split()).strip()


class ProfileData(BaseModel):
    """Complete LinkedIn profile data model with validation"""
    
    # Required fields
    url: str = Field(..., min_length=10, max_length=500)
    name: str = Field(..., min_length=1, max_length=200)
    scraped_at: str = Field(...)
    
    # Optional basic fields
    headline: Optional[str] = Field(None, max_length=500)
    location: Optional[str] = Field(None, max_length=200)
    about: Optional[str] = Field(None, max_length=10000)
    
    # Structured data fields
    experience: List[Union[str, ExperienceEntry]] = Field(default_factory=list, max_items=50)
    education: List[Union[str, EducationEntry]] = Field(default_factory=list, max_items=20)
    skills: List[str] = Field(default_factory=list, max_items=100)
    
    # Metadata fields
    quality_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    quality_level: Optional[DataQuality] = None
    data_completeness: Optional[float] = Field(None, ge=0.0, le=1.0)
    extraction_errors: List[str] = Field(default_factory=list)
    
    @validator('url', pre=True)
    def validate_url(cls, v):
        """Validate LinkedIn profile URL"""
        if not v or not isinstance(v, str):
            raise ValueError("URL is required")
        
        v = str(v).strip()
        if not v.startswith(('http://', 'https://')):
            v = 'https://' + v
        
        if 'linkedin.com/in/' not in v:
            raise ValueError("Must be a LinkedIn profile URL")
        
        return v
    
    @validator('name', pre=True)
    def validate_name(cls, v):
        """Validate and sanitize name"""
        if not v or not isinstance(v, str):
            raise ValueError("Name is required")
        
        name = ' '.join(str(v).split()).strip()
        if len(name) < 1:
            raise ValueError("Name cannot be empty")
        
        return name
    
    @validator('headline', 'location', 'about', pre=True)
    def sanitize_optional_text(cls, v):
        """Sanitize optional text fields"""
        if v is None:
            return None
        return ' '.join(str(v).split()).strip() if v else None
    
    @validator('skills', pre=True)
    def validate_skills(cls, v):
        """Validate and sanitize skills list"""
        if not v:
            return []
        
        if isinstance(v, str):
            v = [v]
        
        skills = []
        for skill in v:
            if skill and isinstance(skill, str):
                sanitized = ' '.join(str(skill).split()).strip()
                if sanitized and len(sanitized) <= 100:
                    skills.append(sanitized)
        
        return list(set(skills))  # Remove duplicates
    
    @validator('scraped_at', pre=True)
    def validate_scraped_at(cls, v):
        """Validate scraped_at timestamp"""
        if not v:
            return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return str(v)
    
    @root_validator
    def calculate_quality_metrics(cls, values):
        """Calculate quality score and level"""
        if 'quality_score' not in values or values['quality_score'] is None:
            values['quality_score'] = cls._calculate_quality_score(values)
        
        # Set quality level based on score
        score = values.get('quality_score', 0.0)
        if score >= 0.8:
            values['quality_level'] = DataQuality.EXCELLENT
        elif score >= 0.6:
            values['quality_level'] = DataQuality.GOOD
        elif score >= 0.4:
            values['quality_level'] = DataQuality.FAIR
        else:
            values['quality_level'] = DataQuality.POOR
        
        # Calculate data completeness
        values['data_completeness'] = cls._calculate_completeness(values)
        
        return values
    
    @staticmethod
    def _calculate_quality_score(values: dict) -> float:
        """Calculate data quality score"""
        score = 0.0
        max_score = 0.0
        
        # Core fields (higher weight)
        core_fields = {
            'name': 0.2,
            'headline': 0.15,
            'location': 0.1,
            'about': 0.15
        }
        
        for field, weight in core_fields.items():
            max_score += weight
            if field in values and values[field]:
                field_value = str(values[field])
                if len(field_value.strip()) > 0:
                    # Bonus for longer, more complete data
                    length_bonus = min(len(field_value) / 100, 1.0) * 0.5
                    score += weight * (0.5 + length_bonus)
        
        # List fields (medium weight)
        list_fields = {
            'experience': 0.2,
            'education': 0.1,
            'skills': 0.1
        }
        
        for field, weight in list_fields.items():
            max_score += weight
            if field in values and isinstance(values[field], list) and len(values[field]) > 0:
                # Score based on number of items
                item_score = min(len(values[field]) / 5, 1.0)  # Max score at 5+ items
                score += weight * item_score
        
        return min(score / max_score if max_score > 0 else 0.0, 1.0)
    
    @staticmethod
    def _calculate_completeness(values: dict) -> float:
        """Calculate data completeness percentage"""
        total_fields = 8  # name, headline, location, about, experience, education, skills, url
        filled_fields = 0
        
        required_fields = ['url', 'name']
        optional_fields = ['headline', 'location', 'about']
        list_fields = ['experience', 'education', 'skills']
        
        # Required fields
        for field in required_fields:
            if field in values and values[field]:
                filled_fields += 1
        
        # Optional fields
        for field in optional_fields:
            if field in values and values[field] and str(values[field]).strip():
                filled_fields += 1
        
        # List fields
        for field in list_fields:
            if field in values and isinstance(values[field], list) and len(values[field]) > 0:
                filled_fields += 1
        
        return filled_fields / total_fields
    
    def to_dict(self) -> dict:
        """Convert to dictionary with proper serialization"""
        data = self.dict()
        
        # Convert experience entries to dict if they're models
        if self.experience:
            data['experience'] = [
                item.dict() if hasattr(item, 'dict') else str(item)
                for item in self.experience
            ]
        
        # Convert education entries to dict if they're models
        if self.education:
            data['education'] = [
                item.dict() if hasattr(item, 'dict') else str(item)
                for item in self.education
            ]
        
        return data
    
    class Config:
        """Pydantic configuration"""
        validate_assignment = True
        extra = "forbid"
        use_enum_values = True


class ScrapingConfig(BaseModel):
    """Configuration model for scraping parameters"""
    
    profile_url: str = Field(..., min_length=10)
    output_path: Optional[str] = Field(None, max_length=500)
    headless: bool = Field(True)
    timeout: int = Field(30, ge=5, le=300)
    max_retries: int = Field(3, ge=1, le=10)
    delay_min: float = Field(1.0, ge=0.1, le=10.0)
    delay_max: float = Field(5.0, ge=1.0, le=30.0)
    user_agent: Optional[str] = Field(None, max_length=500)
    
    @validator('profile_url', pre=True)
    def validate_profile_url(cls, v):
        """Validate LinkedIn profile URL"""
        if not v:
            raise ValueError("Profile URL is required")
        
        v = str(v).strip()
        if not v.startswith(('http://', 'https://')):
            v = 'https://' + v
        
        if 'linkedin.com/in/' not in v:
            raise ValueError("Must be a LinkedIn profile URL")
        
        return v
    
    @validator('output_path', pre=True)
    def validate_output_path(cls, v):
        """Validate output path"""
        if v is None:
            return None
        
        v = str(v).strip()
        if not v:
            return None
        
        # Check for valid extensions
        valid_extensions = ['.json', '.csv', '.xlsx', '.xml']
        if not any(v.lower().endswith(ext) for ext in valid_extensions):
            raise ValueError(f"Output file must have one of these extensions: {valid_extensions}")
        
        return v
    
    @root_validator
    def validate_delay_range(cls, values):
        """Ensure delay_max >= delay_min"""
        delay_min = values.get('delay_min', 1.0)
        delay_max = values.get('delay_max', 5.0)
        
        if delay_max < delay_min:
            values['delay_max'] = delay_min + 1.0
        
        return values
    
    class Config:
        """Pydantic configuration"""
        validate_assignment = True
        extra = "forbid" 