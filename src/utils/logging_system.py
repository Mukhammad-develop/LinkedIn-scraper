"""
Step 7: Advanced Logging and Monitoring System
"""

import logging
import json
from datetime import datetime
from typing import Dict, Any
import psutil
import time

class ScraperMetrics:
    """Performance and usage metrics"""
    def __init__(self):
        self.start_time = time.time()
        self.requests_made = 0
        self.profiles_scraped = 0
        self.errors_count = 0
        self.rate_limit_hits = 0
    
    def get_metrics(self) -> Dict[str, Any]:
        runtime = time.time() - self.start_time
        return {
            'runtime_seconds': runtime,
            'requests_made': self.requests_made,
            'profiles_scraped': self.profiles_scraped,
            'errors_count': self.errors_count,
            'rate_limit_hits': self.rate_limit_hits,
            'requests_per_minute': (self.requests_made / runtime * 60) if runtime > 0 else 0,
            'memory_usage_mb': psutil.Process().memory_info().rss / 1024 / 1024,
            'cpu_percent': psutil.cpu_percent()
        }

class StructuredLogger:
    """Structured logging with JSON format"""
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.metrics = ScraperMetrics()
    
    def log_scraping_start(self, url: str):
        self.logger.info("Scraping started", extra={
            'event': 'scraping_start',
            'url': url,
            'timestamp': datetime.now().isoformat()
        })
    
    def log_scraping_success(self, url: str, quality_score: float):
        self.metrics.profiles_scraped += 1
        self.logger.info("Scraping completed", extra={
            'event': 'scraping_success',
            'url': url,
            'quality_score': quality_score,
            'timestamp': datetime.now().isoformat()
        })
    
    def log_error(self, error: Exception, context: Dict[str, Any] = None):
        self.metrics.errors_count += 1
        self.logger.error(f"Error occurred: {error}", extra={
            'event': 'error',
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context or {},
            'timestamp': datetime.now().isoformat()
        })

# Global logger instance
scraper_logger = StructuredLogger('linkedin_scraper') 