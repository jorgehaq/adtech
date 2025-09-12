# apps/events/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import ImpressionEvent, ClickEvent, ConversionEvent
from .serializers import ImpressionEventSerializer, ClickEventSerializer, ConversionEventSerializer
from apps.analytics.events import (
    replay_events, 
    record_impression_event, 
    record_click_event, 
    record_conversion_event,
    get_event_stream,
    validate_event_sequence
)
from apps.analytics.models import AdEvent
from decimal import Decimal
import logging
from django.conf import settings
from .pubsub import EventPublisher

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def record_impression(request):
    """Record impression event"""
    try:
        data = request.data
        campaign_id = data.get('campaign_id')
        ad_id = data.get('ad_id') 
        user_id = data.get('user_id')
        cost = Decimal(str(data.get('cost', '0.00')))
        
        if not all([campaign_id, ad_id, user_id]):
            return Response({
                'error': 'Missing required fields: campaign_id, ad_id, user_id'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        event = record_impression_event(
            campaign_id, ad_id, user_id, cost, request.user.tenant_id
        )
        
        if event:
            return Response({
                'event_id': event.id,
                'event_type': event.event_type,
                'campaign_id': campaign_id,
                'status': 'recorded',
                'timestamp': event.timestamp
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'error': 'Failed to record impression event'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        logger.error(f"Error recording impression: {str(e)}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def record_click(request):
    """Record click event"""
    try:
        data = request.data
        campaign_id = data.get('campaign_id')
        ad_id = data.get('ad_id')
        user_id = data.get('user_id')
        impression_id = data.get('impression_id')
        
        if not all([campaign_id, ad_id, user_id]):
            return Response({
                'error': 'Missing required fields: campaign_id, ad_id, user_id'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        event = record_click_event(
            campaign_id, ad_id, user_id, request.user.tenant_id, impression_id
        )
        
        if event:
            return Response({
                'event_id': event.id,
                'event_type': event.event_type,
                'campaign_id': campaign_id,
                'status': 'recorded',
                'timestamp': event.timestamp
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'error': 'Failed to record click event'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        logger.error(f"Error recording click: {str(e)}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def record_conversion(request):
    """Record conversion event"""
    try:
        data = request.data
        campaign_id = data.get('campaign_id')
        user_id = data.get('user_id')
        conversion_value = Decimal(str(data.get('conversion_value', '0.00')))
        
        if not all([campaign_id, user_id]):
            return Response({
                'error': 'Missing required fields: campaign_id, user_id'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        event = record_conversion_event(
            campaign_id, user_id, conversion_value, request.user.tenant_id
        )
        
        if event:
            return Response({
                'event_id': event.id,
                'event_type': event.event_type,
                'campaign_id': campaign_id,
                'conversion_value': str(conversion_value),
                'status': 'recorded',
                'timestamp': event.timestamp
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'error': 'Failed to record conversion event'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        logger.error(f"Error recording conversion: {str(e)}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def rebuild_campaign_metrics(request, campaign_id):
    """Rebuild metrics from events - Event Sourcing replay"""
    try:
        replayed_events = replay_events(campaign_id, request.user.tenant_id)
        
        return Response({
            'campaign_id': campaign_id,
            'events_replayed': len(replayed_events),
            'status': 'completed',
            'tenant_id': request.user.tenant_id,
            'message': f'Successfully replayed {len(replayed_events)} events'
        })
        
    except Exception as e:
        logger.error(f"Error rebuilding metrics for campaign {campaign_id}: {str(e)}")
        return Response({
            'error': str(e),
            'campaign_id': campaign_id,
            'status': 'failed'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def event_stream(request, campaign_id):
    """Get event stream for campaign"""
    try:
        limit = int(request.GET.get('limit', 100))
        events = get_event_stream(campaign_id, request.user.tenant_id, limit)
        
        return Response({
            'campaign_id': campaign_id,
            'events': events,
            'total_events': len(events),
            'limit': limit
        })
        
    except Exception as e:
        logger.error(f"Error getting event stream for campaign {campaign_id}: {str(e)}")
        return Response({
            'error': str(e),
            'campaign_id': campaign_id
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def validate_events(request, campaign_id):
    """Validate event sequence integrity"""
    try:
        validation = validate_event_sequence(campaign_id, request.user.tenant_id)
        
        return Response({
            'campaign_id': campaign_id,
            'validation': validation,
            'status': 'valid' if validation['valid'] else 'invalid'
        })
        
    except Exception as e:
        logger.error(f"Error validating events for campaign {campaign_id}: {str(e)}")
        return Response({
            'error': str(e),
            'campaign_id': campaign_id
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def event_stats(request):
    """Get event statistics for tenant"""
    try:
        tenant_id = request.user.tenant_id
        
        # Get event counts by type
        stats = {}
        event_types = ['impression_created', 'click_registered', 'conversion_tracked']
        
        for event_type in event_types:
            count = AdEvent.objects.filter(
                tenant_id=tenant_id,
                event_type=event_type
            ).count()
            stats[event_type] = count
        
        # Total events
        total_events = AdEvent.objects.filter(tenant_id=tenant_id).count()
        
        # Recent events (last hour)
        from django.utils import timezone
        from datetime import timedelta
        
        recent_events = AdEvent.objects.filter(
            tenant_id=tenant_id,
            timestamp__gte=timezone.now() - timedelta(hours=1)
        ).count()
        
        return Response({
            'tenant_id': tenant_id,
            'total_events': total_events,
            'events_last_hour': recent_events,
            'event_counts': stats,
            'event_sourcing_active': True
        })
        
    except Exception as e:
        logger.error(f"Error getting event stats: {str(e)}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def cleanup_events(request):
    """Cleanup old events (admin only)"""
    try:
        # Only allow admin users or superusers
        if not (request.user.is_staff or request.user.role == 'admin'):
            return Response({
                'error': 'Admin privileges required'
            }, status=status.HTTP_403_FORBIDDEN)
        
        days = int(request.GET.get('days', 30))
        
        from django.utils import timezone
        from datetime import timedelta
        
        cutoff_date = timezone.now() - timedelta(days=days)
        
        deleted_count = AdEvent.objects.filter(
            tenant_id=request.user.tenant_id,
            timestamp__lt=cutoff_date
        ).delete()[0]
        
        return Response({
            'deleted_events': deleted_count,
            'cutoff_days': days,
            'tenant_id': request.user.tenant_id
        })
        
    except Exception as e:
        logger.error(f"Error cleaning up events: {str(e)}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_conversion_event(request):
    serializer = ConversionEventSerializer(data=request.data)
    if serializer.is_valid():
        conversion = serializer.save(tenant_id=request.user.tenant_id)
        
        # Event sourcing
        AdEvent.objects.create(
            tenant_id=request.user.tenant_id,
            event_type='conversion_tracked',
            aggregate_id=str(conversion.click.impression.campaign.id),
            payload={
                'conversion_id': conversion.id,
                'click_id': conversion.click.id,
                'value': str(conversion.conversion_value)
            },
            sequence_number=AdEvent.objects.count() + 1
        )
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_click_event(request):
    serializer = ClickEventSerializer(data=request.data)
    if serializer.is_valid():
        click = serializer.save(tenant_id=request.user.tenant_id)
        
        # Event sourcing
        AdEvent.objects.create(
            tenant_id=request.user.tenant_id,
            event_type='click_registered',
            aggregate_id=str(click.impression.campaign.id),
            payload={
                'click_id': click.id,
                'impression_id': click.impression.id
            },
            sequence_number=AdEvent.objects.count() + 1
        )
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_impression_event(request):
    serializer = ImpressionEventSerializer(data=request.data)
    if serializer.is_valid():
        impression = serializer.save(tenant_id=request.user.tenant_id)
        
        # Event sourcing
        AdEvent.objects.create(
            tenant_id=request.user.tenant_id,
            event_type='impression_created',
            aggregate_id=str(impression.campaign.id),
            payload={
                'impression_id': impression.id,
                'ad_id': impression.ad.id,
                'user_id': impression.user_id,
                'cost': str(impression.cost)
            },
            sequence_number=AdEvent.objects.count() + 1
        )

        if settings.DEBUG is False:  # Solo en production
            publisher = EventPublisher()
            publisher.publish_impression_event(
                request.user.tenant_id,
                {
                    'campaign_id': impression.campaign.id,
                    'cost': str(impression.cost),
                    'timestamp': impression.timestamp.isoformat()
                }
            )
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)