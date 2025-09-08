from celery import shared_task
from django.db import connection
from tenacity import retry, stop_after_attempt, wait_exponential
import logging

logger = logging.getLogger(__name__)

@shared_task
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def calculate_daily_metrics(tenant_id):
    """Heavy aggregation job"""
    sql = """
    INSERT INTO analytics_campaignmetrics (tenant_id, campaign_id, date, impressions, clicks, conversions, spend)
    SELECT 
        %s as tenant_id,
        ca.id as campaign_id,
        CURDATE() as date,
        COALESCE(COUNT(ci.id), 0) as impressions,
        0 as clicks,  -- Will be updated when click events exist
        0 as conversions,
        COALESCE(SUM(ci.cost), 0) as spend
    FROM campaigns_campaign ca
    LEFT JOIN campaigns_ad ad ON ad.campaign_id = ca.id AND ad.tenant_id = %s
    LEFT JOIN campaigns_impression ci ON ci.ad_id = ad.id AND ci.tenant_id = %s 
        AND DATE(ci.timestamp) = CURDATE()
    WHERE ca.tenant_id = %s
    GROUP BY ca.id
    ON DUPLICATE KEY UPDATE
        impressions = VALUES(impressions),
        spend = VALUES(spend)
    """
    
    with connection.cursor() as cursor:
        cursor.execute(sql, [tenant_id, tenant_id, tenant_id, tenant_id])
        affected_rows = cursor.rowcount
    
    logger.info(f"Daily metrics calculated for tenant {tenant_id}: {affected_rows} campaigns")
    return {'tenant_id': tenant_id, 'campaigns_processed': affected_rows}

@shared_task
@retry(stop=stop_after_attempt(3))
def process_events_batch(tenant_id, event_ids):
    """Batch event processing"""
    from apps.analytics.models import AdEvent
    
    events = AdEvent.objects.filter(
        id__in=event_ids,
        tenant_id=tenant_id
    ).order_by('sequence_number')
    
    impression_count = 0
    click_count = 0
    conversion_count = 0
    
    for event in events:
        if event.event_type == 'impression_created':
            impression_count += 1
        elif event.event_type == 'click_registered':
            click_count += 1
        elif event.event_type == 'conversion_tracked':
            conversion_count += 1
    
    return {
        'events_processed': len(event_ids),
        'impressions': impression_count,
        'clicks': click_count,
        'conversions': conversion_count
    }

@shared_task
def cleanup_old_events(days=30):
    """Cleanup task for old events"""
    from django.utils import timezone
    from apps.analytics.models import AdEvent
    from datetime import timedelta
    
    cutoff_date = timezone.now() - timedelta(days=days)
    deleted_count = AdEvent.objects.filter(timestamp__lt=cutoff_date).delete()[0]
    
    logger.info(f"Cleaned up {deleted_count} old events older than {days} days")
    return {'deleted_events': deleted_count}

@shared_task
@retry(stop=stop_after_attempt(2))
def generate_campaign_report(tenant_id, campaign_id, report_type='performance'):
    """Generate heavy campaign reports"""
    sql = """
    SELECT 
        DATE(ci.timestamp) as date,
        COUNT(*) as impressions,
        SUM(ci.cost) as spend,
        COUNT(DISTINCT ci.user_id) as unique_users,
        AVG(ci.cost) as avg_cpm
    FROM campaigns_impression ci
    JOIN campaigns_ad ad ON ci.ad_id = ad.id
    WHERE ad.campaign_id = %s AND ci.tenant_id = %s
    GROUP BY DATE(ci.timestamp)
    ORDER BY date DESC
    LIMIT 30
    """
    
    with connection.cursor() as cursor:
        cursor.execute(sql, [campaign_id, tenant_id])
        results = cursor.fetchall()
    
    # Simulate report generation processing time
    import time
    time.sleep(2)  # Heavy computation simulation
    
    return {
        'campaign_id': campaign_id,
        'report_type': report_type,
        'data_points': len(results),
        'date_range': '30_days'
    }