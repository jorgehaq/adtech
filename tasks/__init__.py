from core.celery import app as celery_app
from . import analytics

__all__ = ('celery_app',)