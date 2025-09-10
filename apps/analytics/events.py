from apps.analytics.models import AdEvent, CampaignMetrics
from apps.campaigns.models import Campaign
from django.db import transaction
from collections import defaultdict

def replay_events(aggregate_id, tenant_id):
    """Rebuild metrics from event stream"""
    events = AdEvent.objects.filter(
        aggregate_id=aggregate_id,
        tenant_id=tenant_id
    ).order_by('sequence_number')
    
    # Reset metrics
    CampaignMetrics.objects.filter(
        campaign_id=aggregate_id,
        tenant_id=tenant_id
    ).delete()
    
    # Replay events and rebuild state
    metrics = defaultdict(lambda: {
        'impressions': 0,
        'clicks': 0, 
        'conversions': 0,
        'spend': 0
    })
    
    for event in events:
        date_key = event.timestamp.date()
        
        if event.event_type == 'impression_created':
            metrics[date_key]['impressions'] += 1
            metrics[date_key]['spend'] += float(event.payload.get('cost', 0))
            
        elif event.event_type == 'click_registered':
            metrics[date_key]['clicks'] += 1
            
        elif event.event_type == 'conversion_tracked':
            metrics[date_key]['conversions'] += 1
    
    # Save rebuilt metrics
    campaign = Campaign.objects.get(id=aggregate_id)
    with transaction.atomic():
        for date, data in metrics.items():
            CampaignMetrics.objects.create(
                tenant_id=tenant_id,
                campaign=campaign,
                date=date,
                **data
            )
    
    return len(events)