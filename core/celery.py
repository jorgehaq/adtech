import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.dev')

app = Celery('adtech')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Explicitly include tasks from the tasks package
app.autodiscover_tasks(['tasks'])