from apps.analytics.models import AdEvent, CampaignMetrics
from apps.campaigns.models import Campaign
from django.db import transaction
from collections import defaultdict

# apps/analytics/events.py
def replay_events(aggregate_id, tenant_id):
    """Rebuild metrics from event stream"""
    try:
        events = AdEvent.objects.filter(
            aggregate_id=aggregate_id,
            tenant_id=tenant_id
        ).order_by('sequence_number')
        
        if not events.exists():
            return 0
        
        # Reset metrics
        CampaignMetrics.objects.filter(
            campaign_id=aggregate_id,
            tenant_id=tenant_id
        ).delete()
        
        # Check if campaign exists
        try:
            campaign = Campaign.objects.get(id=aggregate_id, tenant_id=tenant_id)
        except Campaign.DoesNotExist:
            print(f"Campaign {aggregate_id} not found for tenant {tenant_id}")
            return 0
        
        # Rest of replay logic...
        
    except Exception as e:
        print(f"Replay failed: {e}")
        return 0