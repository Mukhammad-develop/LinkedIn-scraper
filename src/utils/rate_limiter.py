"""
Step 5: Rate Limiting and Anti-Detection
Advanced rate limiting, request throttling, and detection evasion
"""

import time
import random
import logging
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from threading import Lock
from collections import deque
from datetime import datetime, timedelta
import json
import os

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Rate limiting configuration"""
    requests_per_minute: int = 10
    requests_per_hour: int = 100
    burst_limit: int = 3
    cooldown_period: int = 300  # 5 minutes
    jitter_range: tuple = (0.5, 2.0)
    progressive_delay: bool = True


class RateLimiter:
    """Advanced rate limiter with burst control and adaptive delays"""
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.request_times = deque()
        self.hourly_requests = deque()
        self.consecutive_requests = 0
        self.last_request_time = 0
        self.lock = Lock()
        self.cooldown_until = None
        
    def can_make_request(self) -> bool:
        """Check if a request can be made now"""
        with self.lock:
            now = time.time()
            
            # Check cooldown period
            if self.cooldown_until and now < self.cooldown_until:
                return False
            
            # Clean old entries
            self._clean_old_entries(now)
            
            # Check per-minute limit
            if len(self.request_times) >= self.config.requests_per_minute:
                return False
            
            # Check per-hour limit
            if len(self.hourly_requests) >= self.config.requests_per_hour:
                return False
            
            # Check burst limit
            if self.consecutive_requests >= self.config.burst_limit:
                if now - self.last_request_time < 60:  # Within last minute
                    return False
            
            return True
    
    def wait_if_needed(self) -> float:
        """Wait if rate limit requires it, return wait time"""
        if self.can_make_request():
            return 0.0
        
        with self.lock:
            now = time.time()
            
            # Calculate required wait time
            wait_time = self._calculate_wait_time(now)
            
            if wait_time > 0:
                # Add jitter to avoid thundering herd
                jitter = random.uniform(*self.config.jitter_range)
                actual_wait = wait_time * jitter
                
                logger.info(f"Rate limit reached, waiting {actual_wait:.2f}s")
                time.sleep(actual_wait)
                
                return actual_wait
        
        return 0.0
    
    def record_request(self):
        """Record that a request was made"""
        with self.lock:
            now = time.time()
            
            self.request_times.append(now)
            self.hourly_requests.append(now)
            
            # Update consecutive counter
            if now - self.last_request_time < 10:  # Within 10 seconds
                self.consecutive_requests += 1
            else:
                self.consecutive_requests = 1
            
            self.last_request_time = now
    
    def trigger_cooldown(self, duration: Optional[int] = None):
        """Trigger cooldown period (e.g., after getting rate limited)"""
        with self.lock:
            cooldown_duration = duration or self.config.cooldown_period
            self.cooldown_until = time.time() + cooldown_duration
            logger.warning(f"Cooldown triggered for {cooldown_duration}s")
    
    def _clean_old_entries(self, now: float):
        """Remove old entries from tracking"""
        # Remove entries older than 1 minute
        while self.request_times and now - self.request_times[0] > 60:
            self.request_times.popleft()
        
        # Remove entries older than 1 hour
        while self.hourly_requests and now - self.hourly_requests[0] > 3600:
            self.hourly_requests.popleft()
    
    def _calculate_wait_time(self, now: float) -> float:
        """Calculate how long to wait"""
        wait_times = []
        
        # Wait for cooldown
        if self.cooldown_until and now < self.cooldown_until:
            wait_times.append(self.cooldown_until - now)
        
        # Wait for per-minute limit
        if len(self.request_times) >= self.config.requests_per_minute:
            oldest_request = self.request_times[0]
            wait_times.append(60 - (now - oldest_request))
        
        # Wait for burst limit
        if self.consecutive_requests >= self.config.burst_limit:
            if now - self.last_request_time < 60:
                wait_times.append(60 - (now - self.last_request_time))
        
        return max(wait_times) if wait_times else 0.0


class AntiDetectionManager:
    """Advanced anti-detection techniques"""
    
    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101'
        ]
        
        self.screen_resolutions = [
            (1920, 1080), (1366, 768), (1440, 900), (1536, 864), (1024, 768)
        ]
        
        self.request_delays = {
            'page_load': (2, 5),
            'scroll': (0.5, 1.5),
            'click': (0.2, 0.8),
            'type': (0.1, 0.3)
        }
    
    def get_random_user_agent(self) -> str:
        """Get random user agent"""
        return random.choice(self.user_agents)
    
    def get_random_viewport(self) -> tuple:
        """Get random viewport size"""
        return random.choice(self.screen_resolutions)
    
    def get_human_delay(self, action_type: str = 'page_load') -> float:
        """Get human-like delay for actions"""
        delay_range = self.request_delays.get(action_type, (1, 3))
        return random.uniform(*delay_range)
    
    def apply_browser_stealth(self, driver):
        """Apply stealth techniques to browser"""
        try:
            # Remove webdriver property
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Override plugins
            driver.execute_script("""
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
            """)
            
            # Override languages
            driver.execute_script("""
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en']
                });
            """)
            
            # Override permissions
            driver.execute_script("""
                const originalQuery = window.navigator.permissions.query;
                return window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
            """)
            
        except Exception as e:
            logger.warning(f"Could not apply some stealth techniques: {e}")
    
    def simulate_human_behavior(self, driver, action: str = 'browse'):
        """Simulate human browsing behavior"""
        try:
            if action == 'browse':
                # Random scrolling
                scroll_pause = self.get_human_delay('scroll')
                driver.execute_script(f"""
                    window.scrollTo(0, {random.randint(100, 500)});
                    setTimeout(() => {{
                        window.scrollTo(0, {random.randint(600, 1200)});
                    }}, {scroll_pause * 1000});
                """)
                
            elif action == 'mouse_movement':
                # Simulate mouse movements
                from selenium.webdriver.common.action_chains import ActionChains
                actions = ActionChains(driver)
                
                # Random mouse movements
                for _ in range(random.randint(1, 3)):
                    x_offset = random.randint(-100, 100)
                    y_offset = random.randint(-50, 50)
                    actions.move_by_offset(x_offset, y_offset)
                
                actions.perform()
                
        except Exception as e:
            logger.debug(f"Human behavior simulation failed: {e}")


class RequestThrottler:
    """Request throttling with adaptive delays"""
    
    def __init__(self, base_delay: float = 1.0, max_delay: float = 30.0):
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.current_delay = base_delay
        self.success_count = 0
        self.failure_count = 0
        self.last_request_time = 0
    
    def before_request(self):
        """Call before making a request"""
        now = time.time()
        elapsed = now - self.last_request_time
        
        if elapsed < self.current_delay:
            sleep_time = self.current_delay - elapsed
            logger.debug(f"Throttling request, sleeping {sleep_time:.2f}s")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def after_request(self, success: bool):
        """Call after request completion"""
        if success:
            self.success_count += 1
            self.failure_count = 0
            
            # Gradually reduce delay on success
            if self.success_count >= 5:
                self.current_delay = max(
                    self.base_delay,
                    self.current_delay * 0.9
                )
                self.success_count = 0
        else:
            self.failure_count += 1
            self.success_count = 0
            
            # Increase delay on failure
            self.current_delay = min(
                self.max_delay,
                self.current_delay * (1.5 + self.failure_count * 0.1)
            )
            
            logger.warning(f"Request failed, increased delay to {self.current_delay:.2f}s")


class SessionManager:
    """Manage browser sessions with rotation"""
    
    def __init__(self, session_duration: int = 1800):  # 30 minutes
        self.session_duration = session_duration
        self.session_start = None
        self.requests_in_session = 0
        self.max_requests_per_session = random.randint(50, 100)
    
    def should_rotate_session(self) -> bool:
        """Check if session should be rotated"""
        if not self.session_start:
            return False
        
        now = time.time()
        session_age = now - self.session_start
        
        # Rotate if session too old or too many requests
        return (session_age > self.session_duration or 
                self.requests_in_session >= self.max_requests_per_session)
    
    def start_new_session(self):
        """Start a new session"""
        self.session_start = time.time()
        self.requests_in_session = 0
        self.max_requests_per_session = random.randint(50, 100)
        logger.info("Started new browser session")
    
    def record_request(self):
        """Record a request in current session"""
        if not self.session_start:
            self.start_new_session()
        
        self.requests_in_session += 1


class DetectionAvoidance:
    """Detection avoidance strategies"""
    
    @staticmethod
    def add_chrome_options(options):
        """Add anti-detection Chrome options"""
        # Basic stealth options
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Additional stealth options
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-plugins')
        options.add_argument('--disable-images')
        options.add_argument('--disable-javascript')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-web-security')
        options.add_argument('--allow-running-insecure-content')
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--ignore-ssl-errors')
        options.add_argument('--ignore-certificate-errors-spki-list')
        
        # Random user agent
        anti_detection = AntiDetectionManager()
        user_agent = anti_detection.get_random_user_agent()
        options.add_argument(f'--user-agent={user_agent}')
        
        # Random window size
        width, height = anti_detection.get_random_viewport()
        options.add_argument(f'--window-size={width},{height}')
        
        return options
    
    @staticmethod
    def setup_request_headers() -> Dict[str, str]:
        """Generate realistic request headers"""
        return {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }


class RateLimitingManager:
    """Main manager combining all rate limiting and anti-detection features"""
    
    def __init__(self, config: Optional[RateLimitConfig] = None):
        self.config = config or RateLimitConfig()
        self.rate_limiter = RateLimiter(self.config)
        self.anti_detection = AntiDetectionManager()
        self.throttler = RequestThrottler()
        self.session_manager = SessionManager()
        self.stats = {
            'requests_made': 0,
            'rate_limit_waits': 0,
            'cooldowns_triggered': 0,
            'sessions_rotated': 0
        }
    
    def prepare_request(self, driver=None) -> Dict[str, any]:
        """Prepare for making a request"""
        # Check rate limits
        wait_time = self.rate_limiter.wait_if_needed()
        if wait_time > 0:
            self.stats['rate_limit_waits'] += 1
        
        # Apply throttling
        self.throttler.before_request()
        
        # Check session rotation
        if self.session_manager.should_rotate_session():
            self.stats['sessions_rotated'] += 1
            return {'rotate_session': True}
        
        # Apply anti-detection if driver provided
        if driver:
            self.anti_detection.apply_browser_stealth(driver)
            
            # Simulate human behavior occasionally
            if random.random() < 0.3:  # 30% chance
                self.anti_detection.simulate_human_behavior(driver)
        
        return {'rotate_session': False}
    
    def record_request_result(self, success: bool, detected: bool = False):
        """Record the result of a request"""
        self.rate_limiter.record_request()
        self.session_manager.record_request()
        self.throttler.after_request(success)
        self.stats['requests_made'] += 1
        
        # Trigger cooldown if detected
        if detected:
            self.rate_limiter.trigger_cooldown()
            self.stats['cooldowns_triggered'] += 1
            logger.warning("Detection suspected, triggering cooldown")
    
    def get_stats(self) -> Dict[str, any]:
        """Get rate limiting statistics"""
        return {
            **self.stats,
            'current_delay': self.throttler.current_delay,
            'session_requests': self.session_manager.requests_in_session,
            'in_cooldown': bool(self.rate_limiter.cooldown_until and 
                              time.time() < self.rate_limiter.cooldown_until)
        }
    
    def save_stats(self, filepath: str):
        """Save statistics to file"""
        try:
            stats_data = {
                'timestamp': datetime.now().isoformat(),
                'stats': self.get_stats(),
                'config': {
                    'requests_per_minute': self.config.requests_per_minute,
                    'requests_per_hour': self.config.requests_per_hour,
                    'burst_limit': self.config.burst_limit
                }
            }
            
            with open(filepath, 'w') as f:
                json.dump(stats_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save stats: {e}") 