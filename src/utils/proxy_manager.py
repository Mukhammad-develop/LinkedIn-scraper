"""
Step 10: Proxy Rotation and Management
Proxy rotation, testing, and failover management
"""

import random
import requests
from typing import List, Optional, Dict
import logging

logger = logging.getLogger(__name__)

class ProxyManager:
    """Proxy rotation and management"""
    
    def __init__(self, proxy_list: List[str] = None):
        self.proxy_list = proxy_list or []
        self.working_proxies = []
        self.current_proxy_index = 0
        self.test_url = "http://httpbin.org/ip"
    
    def test_proxy(self, proxy: str, timeout: int = 10) -> bool:
        """Test if proxy is working"""
        try:
            proxies = {'http': proxy, 'https': proxy}
            response = requests.get(self.test_url, proxies=proxies, timeout=timeout)
            return response.status_code == 200
        except Exception as e:
            logger.debug(f"Proxy {proxy} failed test: {e}")
            return False
    
    def validate_proxies(self):
        """Test all proxies and keep only working ones"""
        self.working_proxies = []
        for proxy in self.proxy_list:
            if self.test_proxy(proxy):
                self.working_proxies.append(proxy)
                logger.info(f"Proxy {proxy} is working")
        
        logger.info(f"Found {len(self.working_proxies)} working proxies out of {len(self.proxy_list)}")
    
    def get_next_proxy(self) -> Optional[str]:
        """Get next proxy in rotation"""
        if not self.working_proxies:
            return None
        
        proxy = self.working_proxies[self.current_proxy_index]
        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.working_proxies)
        return proxy
    
    def get_random_proxy(self) -> Optional[str]:
        """Get random proxy"""
        if not self.working_proxies:
            return None
        return random.choice(self.working_proxies)
    
    def remove_proxy(self, proxy: str):
        """Remove failed proxy from working list"""
        if proxy in self.working_proxies:
            self.working_proxies.remove(proxy)
            logger.warning(f"Removed failed proxy: {proxy}")

# Global proxy manager
proxy_manager = ProxyManager() 