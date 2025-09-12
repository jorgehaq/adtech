# apps/analytics/repositories/performance.py
from functools import wraps
import time
import logging

logger = logging.getLogger(__name__)

def monitor_query_performance(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time = time.time() - start_time
        
        if execution_time > 1.0:  # Log slow queries
            logger.warning(f"Slow query: {func.__name__} took {execution_time:.2f}s")
        
        return result
    return wrapper