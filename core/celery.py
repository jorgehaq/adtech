import os
from celery import Celery

settings_module = os.environ.get('DJANGO_SETTINGS_MODULE', 'core.settings.local')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings_module)

app = Celery('adtech')
app.config_from_object('django.conf:settings', namespace='CELERY')

# Force Celery to use the Redis transport
app.conf.update(
    broker_transport_options={'client_class': 'redis'},
)

app.autodiscover_tasks()
app.autodiscover_tasks(['tasks'])