"""
Step 9: Async Processing
Concurrent scraping of multiple profiles with queue management
"""

import asyncio
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor
import logging

logger = logging.getLogger(__name__)

class AsyncProfileProcessor:
    """Async processor for multiple profiles"""
    
    def __init__(self, max_workers: int = 3):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
    
    async def process_profiles(self, urls: List[str], scraper) -> List[Dict[str, Any]]:
        """Process multiple profiles concurrently"""
        tasks = []
        for url in urls:
            task = asyncio.create_task(self._scrape_profile_async(url, scraper))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and return successful results
        successful_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Failed to scrape {urls[i]}: {result}")
            else:
                successful_results.append(result)
        
        return successful_results
    
    async def _scrape_profile_async(self, url: str, scraper) -> Dict[str, Any]:
        """Async wrapper for profile scraping"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, scraper.scrape_profile, url)
    
    def close(self):
        """Close the executor"""
        self.executor.shutdown(wait=True)

# Global async processor
async_processor = AsyncProfileProcessor() 