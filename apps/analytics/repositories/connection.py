# apps/analytics/repositories/connection.py
from django.db import connections
from contextlib import contextmanager
import time

@contextmanager
def get_analytics_cursor():
    """Optimized cursor for heavy analytics queries"""
    connection = connections['default']
    with connection.cursor() as cursor:
        try:
            cursor.execute("SET SESSION query_cache_type = ON")
        except Exception:
            pass  # Query cache removed in MySQL 8.0+
        cursor.execute("SET SESSION tmp_table_size = 268435456")  # 256MB
        yield cursor

@contextmanager
def optimized_analytics_cursor():
    connection = connections['default']
    with connection.cursor() as cursor:
        # Query optimization for analytics
        try:
            cursor.execute("SET SESSION query_cache_type = ON")
        except Exception:
            pass  # Query cache removed in MySQL 8.0+
        cursor.execute("SET SESSION tmp_table_size = 268435456")  # 256MB
        cursor.execute("SET SESSION max_heap_table_size = 268435456")
        yield cursor