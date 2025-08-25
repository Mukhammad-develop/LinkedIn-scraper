"""
Step 8: Database Integration
SQLite and PostgreSQL support for storing scraped data
"""

import sqlite3
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Database manager with SQLite support"""
    
    def __init__(self, db_path: str = "data/profiles.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT UNIQUE NOT NULL,
                    name TEXT,
                    headline TEXT,
                    location TEXT,
                    about TEXT,
                    experience TEXT,
                    education TEXT,
                    skills TEXT,
                    quality_score REAL,
                    scraped_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS scraping_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT UNIQUE,
                    profiles_count INTEGER,
                    success_count INTEGER,
                    error_count INTEGER,
                    start_time TIMESTAMP,
                    end_time TIMESTAMP,
                    duration_seconds INTEGER
                )
            """)
    
    def save_profile(self, profile_data: Dict[str, Any]) -> bool:
        """Save profile data to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO profiles 
                    (url, name, headline, location, about, experience, education, skills, quality_score, scraped_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    profile_data.get('url'),
                    profile_data.get('name'),
                    profile_data.get('headline'),
                    profile_data.get('location'),
                    profile_data.get('about'),
                    json.dumps(profile_data.get('experience', [])),
                    json.dumps(profile_data.get('education', [])),
                    json.dumps(profile_data.get('skills', [])),
                    profile_data.get('quality_score'),
                    profile_data.get('scraped_at')
                ))
            return True
        except Exception as e:
            logger.error(f"Failed to save profile to database: {e}")
            return False
    
    def get_profile(self, url: str) -> Optional[Dict[str, Any]]:
        """Get profile by URL"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT * FROM profiles WHERE url = ?", (url,))
                row = cursor.fetchone()
                if row:
                    columns = [desc[0] for desc in cursor.description]
                    return dict(zip(columns, row))
            return None
        except Exception as e:
            logger.error(f"Failed to get profile from database: {e}")
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM profiles")
                total_profiles = cursor.fetchone()[0]
                
                cursor = conn.execute("SELECT AVG(quality_score) FROM profiles WHERE quality_score IS NOT NULL")
                avg_quality = cursor.fetchone()[0] or 0
                
                return {
                    'total_profiles': total_profiles,
                    'average_quality_score': round(avg_quality, 2)
                }
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {'total_profiles': 0, 'average_quality_score': 0}

# Global database instance
db_manager = DatabaseManager() 