# apps/analytics/repositories/base.py
from abc import ABC, abstractmethod
from typing import Dict, List, Any

class BaseAnalyticsRepository(ABC):
    @abstractmethod
    def get_metrics(self, tenant_id: int, **kwargs) -> Dict[str, Any]:
        pass

class MySQLAnalyticsRepository(BaseAnalyticsRepository):
    # Tu implementación actual