from celery import shared_task
from django.db.models import Sum, Count, F
from apps.campaigns.models import Campaign, Impression

@shared_task
def aggregate_daily_metrics(tenant_id):
    """Aggregate daily metrics per campaign for a tenant."""
    # Suponiendo que Impression tiene fields: campaign, timestamp, cost, tenant_id
    results = (
        Impression.objects.filter(tenant_id=tenant_id)
        .annotate(campaign_id=F('ad__campaign_id'))
        .values('campaign_id', 'timestamp__date')
        .annotate(
            impressions=Count('id'),
            total_cost=Sum('cost')
        )
        .order_by('campaign_id', 'timestamp__date')
    )
    # (Opcional) Puedes guardar en tabla de agregados si existe, o solo loggear
    print(f"[Celery] Aggregated {len(results)} daily metrics for tenant {tenant_id}")
    return list(results)
