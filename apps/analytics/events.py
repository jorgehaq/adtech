# apps/analytics/events.py
from apps.analytics.models import AdEvent, CampaignMetrics
from apps.campaigns.models import Campaign, Impression
from django.db import transaction
from django.utils import timezone
from collections import defaultdict
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

def replay_events(campaign_id, tenant_id):
    """Rebuild metrics from events - functional implementation"""
    try:
        campaign_id_str = str(campaign_id)
        
        # Get all events for this campaign, ordered by sequence
        events = AdEvent.objects.filter(
            aggregate_id=campaign_id_str,
            tenant_id=tenant_id
        ).order_by('sequence_number', 'timestamp')
        
        if not events.exists():
            logger.info(f"No events found for campaign {campaign_id}")
            return []
        
        # Initialize metrics
        metrics = {
            'total_impressions': 0,
            'total_clicks': 0,
            'total_conversions': 0,
            'total_spend': Decimal('0.00'),
            'unique_users': set(),
            'daily_metrics': defaultdict(lambda: {
                'impressions': 0,
                'clicks': 0,
                'spend': Decimal('0.00'),
                'users': set()
            })
        }
        
        # Replay events in sequence
        replayed_events = []
        for event in events:
            event_date = event.timestamp.date()
            payload = event.payload or {}
            
            if event.event_type == 'impression_created':
                metrics['total_impressions'] += 1
                metrics['daily_metrics'][event_date]['impressions'] += 1
                
                # Extract cost and user_id from payload
                cost = Decimal(str(payload.get('cost', '0.00')))
                metrics['total_spend'] += cost
                metrics['daily_metrics'][event_date]['spend'] += cost
                
                user_id = payload.get('user_id')
                if user_id:
                    metrics['unique_users'].add(user_id)
                    metrics['daily_metrics'][event_date]['users'].add(user_id)
                    
            elif event.event_type == 'click_registered':
                metrics['total_clicks'] += 1
                metrics['daily_metrics'][event_date]['clicks'] += 1
                
                user_id = payload.get('user_id')
                if user_id:
                    metrics['unique_users'].add(user_id)
                    metrics['daily_metrics'][event_date]['users'].add(user_id)
                    
            elif event.event_type == 'conversion_tracked':
                metrics['total_conversions'] += 1
                
                user_id = payload.get('user_id')
                if user_id:
                    metrics['unique_users'].add(user_id)
            
            replayed_events.append({
                'event_id': event.id,
                'event_type': event.event_type,
                'timestamp': event.timestamp,
                'processed': True
            })
        
        # Update or create campaign metrics
        with transaction.atomic():
            # Clear existing metrics for this campaign
            CampaignMetrics.objects.filter(
                campaign_id=campaign_id,
                tenant_id=tenant_id
            ).delete()
            
            # Create daily metrics
            for date, daily_data in metrics['daily_metrics'].items():
                CampaignMetrics.objects.create(
                    tenant_id=tenant_id,
                    campaign_id=campaign_id,
                    date=date,
                    impressions=daily_data['impressions'],
                    clicks=daily_data['clicks'],
                    conversions=0,  # Will be calculated separately
                    spend=daily_data['spend'],
                    unique_users=len(daily_data['users'])
                )
        
        logger.info(f"Replayed {len(replayed_events)} events for campaign {campaign_id}")
        return replayed_events
        
    except Exception as e:
        logger.error(f"Error replaying events for campaign {campaign_id}: {str(e)}")
        return []


def emit_event(event_type, aggregate_id, payload, tenant_id):
    """Emit new event to event store"""
    try:
        # Get next sequence number for this aggregate
        last_sequence = AdEvent.objects.filter(
            aggregate_id=str(aggregate_id),
            tenant_id=tenant_id
        ).aggregate(
            max_seq=models.Max('sequence_number')
        )['max_seq'] or 0
        
        # Create the event
        event = AdEvent.objects.create(
            tenant_id=tenant_id,
            event_type=event_type,
            aggregate_id=str(aggregate_id),
            payload=payload,
            sequence_number=last_sequence + 1,
            timestamp=timezone.now()
        )
        
        logger.info(f"Event emitted: {event_type} for {aggregate_id}")
        return event
        
    except Exception as e:
        logger.error(f"Error emitting event {event_type}: {str(e)}")
        return None


def record_impression_event(campaign_id, ad_id, user_id, cost, tenant_id):
    """Record impression with event sourcing"""
    payload = {
        'campaign_id': campaign_id,
        'ad_id': ad_id,
        'user_id': user_id,
        'cost': str(cost),
        'timestamp': timezone.now().isoformat()
    }
    
    # Emit the event
    event = emit_event('impression_created', campaign_id, payload, tenant_id)
    
    # Also create traditional record for queries
    try:
        from apps.campaigns.models import Ad
        ad = Ad.objects.get(id=ad_id, tenant_id=tenant_id)
        
        Impression.objects.create(
            tenant_id=tenant_id,
            ad=ad,
            user_id=user_id,
            cost=cost,
            timestamp=timezone.now()
        )
    except Exception as e:
        logger.error(f"Error creating impression record: {str(e)}")
    
    return event


def record_click_event(campaign_id, ad_id, user_id, tenant_id, impression_id=None):
    """Record click with event sourcing"""
    payload = {
        'campaign_id': campaign_id,
        'ad_id': ad_id,
        'user_id': user_id,
        'impression_id': impression_id,
        'timestamp': timezone.now().isoformat()
    }
    
    return emit_event('click_registered', campaign_id, payload, tenant_id)


def record_conversion_event(campaign_id, user_id, conversion_value, tenant_id):
    """Record conversion with event sourcing"""
    payload = {
        'campaign_id': campaign_id,
        'user_id': user_id,
        'conversion_value': str(conversion_value),
        'timestamp': timezone.now().isoformat()
    }
    
    return emit_event('conversion_tracked', campaign_id, payload, tenant_id)


def get_event_stream(campaign_id, tenant_id, limit=100):
    """Get event stream for real-time monitoring"""
    events = AdEvent.objects.filter(
        aggregate_id=str(campaign_id),
        tenant_id=tenant_id
    ).order_by('-timestamp')[:limit]
    
    return [{
        'event_id': event.id,
        'event_type': event.event_type,
        'timestamp': event.timestamp,
        'payload': event.payload,
        'sequence_number': event.sequence_number
    } for event in events]


def validate_event_sequence(campaign_id, tenant_id):
    """Validate event sequence integrity"""
    events = AdEvent.objects.filter(
        aggregate_id=str(campaign_id),
        tenant_id=tenant_id
    ).order_by('sequence_number')
    
    expected_sequence = 1
    gaps = []
    
    for event in events:
        if event.sequence_number != expected_sequence:
            gaps.append({
                'expected': expected_sequence,
                'found': event.sequence_number,
                'event_id': event.id
            })
        expected_sequence = event.sequence_number + 1
    
    return {
        'valid': len(gaps) == 0,
        'gaps': gaps,
        'total_events': events.count(),
        'last_sequence': expected_sequence - 1
    }


# Import here to avoid circular imports
from django.db import models