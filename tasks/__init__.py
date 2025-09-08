from core.celery import app as celery_app

__all__ = ('celery_app',)

# Register tasks explicitly
from .analytics import calculate_daily_metrics, process_events_batch, cleanup_old_events, generate_campaign_report

# Register periodic tasks
from celery.schedules import crontab
from django.conf import settings

if hasattr(settings, 'CELERY_BEAT_SCHEDULE'):
    celery_app.conf.beat_schedule = {
        'calculate-daily-metrics': {
            'task': 'tasks.analytics.calculate_daily_metrics',
            'schedule': crontab(hour=1, minute=0),  # Daily at 1 AM
            'args': (1,)  # Default tenant_id
        },
        'cleanup-old-events': {
            'task': 'tasks.analytics.cleanup_old_events',
            'schedule': crontab(hour=2, minute=0, day_of_week=0),  # Weekly
        },
    }