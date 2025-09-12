# apps/analytics/repositories/cached.py
from django.core.cache import cache
from functools import wraps

def cache_heavy_query(timeout=300):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"analytics:{func.__name__}:{hash(str(args) + str(kwargs))}"
            result = cache.get(cache_key)
            if result is None:
                result = func(*args, **kwargs)
                cache.set(cache_key, result, timeout)
            return result
        return wrapper
    return decorator