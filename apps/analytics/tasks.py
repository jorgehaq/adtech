from celery import shared_task
from tenacity import retry, stop_after_attempt

@shared_task
@retry(stop=stop_after_attempt(3))
def calculate_daily_metrics(tenant_id, date):
    # Cálculo pesado de métricas
    pass

@shared_task
def process_events_batch(event_ids):
    # Procesamiento batch
    pass