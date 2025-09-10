# apps/campaigns/circuit_breaker.py
import time
from enum import Enum
from django.core.cache import cache
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open" 
    HALF_OPEN = "half_open"

class CircuitBreaker:
    def __init__(self, failure_threshold=5, recovery_timeout=60, expected_exception=Exception):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.name = self.__class__.__name__
        
    def _get_cache_key(self, func_name):
        return f"circuit_breaker:{func_name}"
        
    def _get_state(self, func_name):
        data = cache.get(self._get_cache_key(func_name), {
            'state': CircuitState.CLOSED.value,
            'failure_count': 0,
            'last_failure_time': None
        })
        return data
        
    def _set_state(self, func_name, state_data):
        cache.set(self._get_cache_key(func_name), state_data, 300)
        
    def _should_attempt_reset(self, state_data):
        if state_data['state'] != CircuitState.OPEN.value:
            return False
        return time.time() - state_data['last_failure_time'] >= self.recovery_timeout
        
    def __call__(self, func):
        def wrapper(*args, **kwargs):
            func_name = f"{func.__module__}.{func.__name__}"
            state_data = self._get_state(func_name)
            
            # Circuit OPEN - fail fast
            if state_data['state'] == CircuitState.OPEN.value:
                if not self._should_attempt_reset(state_data):
                    logger.warning(f"Circuit breaker OPEN for {func_name}")
                    return self._fallback_response(func_name, *args, **kwargs)
                else:
                    # Transition to HALF_OPEN
                    state_data['state'] = CircuitState.HALF_OPEN.value
                    self._set_state(func_name, state_data)
                    
            try:
                result = func(*args, **kwargs)
                
                # Success - reset if needed
                if state_data['state'] != CircuitState.CLOSED.value:
                    self._reset_circuit(func_name)
                    logger.info(f"Circuit breaker CLOSED for {func_name}")
                    
                return result
                
            except self.expected_exception as e:
                logger.error(f"Circuit breaker failure in {func_name}: {e}")
                return self._record_failure(func_name, state_data, *args, **kwargs)
                
        return wrapper
        
    def _record_failure(self, func_name, state_data, *args, **kwargs):
        state_data['failure_count'] += 1
        state_data['last_failure_time'] = time.time()
        
        if state_data['failure_count'] >= self.failure_threshold:
            state_data['state'] = CircuitState.OPEN.value
            logger.error(f"Circuit breaker OPENED for {func_name}")
            
        self._set_state(func_name, state_data)
        return self._fallback_response(func_name, *args, **kwargs)
        
    def _reset_circuit(self, func_name):
        self._set_state(func_name, {
            'state': CircuitState.CLOSED.value,
            'failure_count': 0,
            'last_failure_time': None
        })
        
    def _fallback_response(self, func_name, *args, **kwargs):
        # Return cached data or empty response
        cache_key = f"fallback:{func_name}:{hash(str(args))}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            logger.info(f"Returning cached fallback for {func_name}")
            return cached_result
            
        # Default fallback
        return [] if 'get_queryset' in func_name else None

# Usage in views
@CircuitBreaker(failure_threshold=3, recovery_timeout=30)
def get_queryset(self):
    return Campaign.objects.filter(tenant_id=self.request.user.tenant_id)