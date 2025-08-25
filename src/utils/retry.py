"""
Step 2: Retry Decorator with Exponential Backoff
Advanced retry mechanisms for robust scraping
"""

import time
import random
import logging
from functools import wraps
from typing import Tuple, Type, Union, Callable, Any

from .exceptions import (
    LinkedInScraperError, NetworkError, RateLimitError, 
    BrowserError, MaxRetriesExceededError
)

logger = logging.getLogger(__name__)


def exponential_backoff(base_delay: float = 1.0, max_delay: float = 60.0, 
                       exponential_base: float = 2.0, jitter: bool = True) -> float:
    """
    Calculate exponential backoff delay with optional jitter
    
    Args:
        base_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential calculation
        jitter: Whether to add random jitter
    
    Returns:
        Calculated delay in seconds
    """
    def _calculate_delay(attempt: int) -> float:
        delay = min(base_delay * (exponential_base ** attempt), max_delay)
        
        if jitter:
            # Add ±25% jitter to avoid thundering herd
            jitter_range = delay * 0.25
            delay += random.uniform(-jitter_range, jitter_range)
        
        return max(delay, 0.1)  # Minimum 0.1 second delay
    
    return _calculate_delay


def retry(max_attempts: int = 3,
          delay_func: Callable[[int], float] = None,
          retry_on: Tuple[Type[Exception], ...] = None,
          stop_on: Tuple[Type[Exception], ...] = None,
          before_retry: Callable = None,
          reraise_as: Type[Exception] = None):
    """
    Decorator for retrying functions with exponential backoff
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay_func: Function to calculate delay based on attempt number
        retry_on: Tuple of exception types to retry on
        stop_on: Tuple of exception types to never retry on
        before_retry: Callback function called before each retry
        reraise_as: Exception type to reraise final failure as
    
    Returns:
        Decorated function with retry logic
    """
    if delay_func is None:
        delay_func = exponential_backoff()
    
    if retry_on is None:
        retry_on = (NetworkError, RateLimitError, BrowserError, ConnectionError, TimeoutError)
    
    if stop_on is None:
        stop_on = (KeyboardInterrupt, SystemExit)
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    logger.debug(f"Attempting {func.__name__} (attempt {attempt + 1}/{max_attempts})")
                    result = func(*args, **kwargs)
                    
                    if attempt > 0:
                        logger.info(f"Successfully executed {func.__name__} after {attempt + 1} attempts")
                    
                    return result
                
                except stop_on as e:
                    logger.error(f"Non-retryable error in {func.__name__}: {e}")
                    raise
                
                except retry_on as e:
                    last_exception = e
                    
                    if attempt == max_attempts - 1:
                        # Last attempt failed
                        break
                    
                    delay = delay_func(attempt)
                    
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_attempts} failed for {func.__name__}: {e}. "
                        f"Retrying in {delay:.2f} seconds..."
                    )
                    
                    # Call before_retry callback if provided
                    if before_retry:
                        try:
                            before_retry(attempt, e, delay)
                        except Exception as callback_error:
                            logger.error(f"Error in before_retry callback: {callback_error}")
                    
                    time.sleep(delay)
                
                except Exception as e:
                    # Unexpected error type
                    logger.error(f"Unexpected error in {func.__name__}: {e}")
                    if attempt == max_attempts - 1:
                        last_exception = e
                        break
                    
                    # Treat as retryable with shorter delay
                    delay = delay_func(attempt) * 0.5
                    logger.warning(f"Treating unexpected error as retryable. Retrying in {delay:.2f} seconds...")
                    time.sleep(delay)
                    last_exception = e
            
            # All attempts failed
            error_msg = f"Failed to execute {func.__name__} after {max_attempts} attempts"
            
            if reraise_as:
                raise reraise_as(
                    error_msg,
                    attempts=max_attempts,
                    last_error=last_exception
                )
            else:
                raise MaxRetriesExceededError(
                    error_msg,
                    attempts=max_attempts,
                    last_error=last_exception
                )
        
        return wrapper
    return decorator


class CircuitBreaker:
    """
    Circuit breaker pattern implementation to prevent cascading failures
    """
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 60.0,
                 expected_exception: Type[Exception] = Exception):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
    
    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if self.state == 'OPEN':
                if self._should_attempt_reset():
                    self.state = 'HALF_OPEN'
                    logger.info(f"Circuit breaker for {func.__name__} is HALF_OPEN, attempting reset")
                else:
                    raise LinkedInScraperError(
                        f"Circuit breaker is OPEN for {func.__name__}. "
                        f"Try again after {self.recovery_timeout} seconds."
                    )
            
            try:
                result = func(*args, **kwargs)
                self._on_success()
                return result
            
            except self.expected_exception as e:
                self._on_failure()
                raise
        
        return wrapper
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if self.last_failure_time is None:
            return True
        
        return time.time() - self.last_failure_time >= self.recovery_timeout
    
    def _on_success(self):
        """Reset circuit breaker on successful execution"""
        self.failure_count = 0
        self.state = 'CLOSED'
        logger.debug("Circuit breaker reset to CLOSED state")
    
    def _on_failure(self):
        """Handle failure and potentially open circuit"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = 'OPEN'
            logger.warning(
                f"Circuit breaker OPENED after {self.failure_count} failures. "
                f"Recovery timeout: {self.recovery_timeout} seconds"
            )


def with_circuit_breaker(failure_threshold: int = 5, recovery_timeout: float = 60.0):
    """
    Decorator to apply circuit breaker pattern
    
    Args:
        failure_threshold: Number of failures before opening circuit
        recovery_timeout: Time to wait before attempting reset
    
    Returns:
        Circuit breaker decorator
    """
    def decorator(func: Callable) -> Callable:
        breaker = CircuitBreaker(failure_threshold, recovery_timeout, LinkedInScraperError)
        return breaker(func)
    
    return decorator 