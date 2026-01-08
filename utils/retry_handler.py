"""Retry Handler - Exponential backoff for transient errors"""
import time
import logging
from functools import wraps

logger = logging.getLogger(__name__)

def with_retry(max_attempts=3, base_delay=1, max_delay=60):
    """Decorator for retrying transient failures"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    logger.warning(f'Attempt {attempt+1} failed, retrying in {delay}s')
                    time.sleep(delay)
        return wrapper
    return decorator
