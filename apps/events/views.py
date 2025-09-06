from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import ImpressionEvent, ClickEvent, ConversionEvent
from .serializers import ImpressionEventSerializer, ClickEventSerializer, ConversionEventSerializer
from apps.analytics.models import AdEvent

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

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_event_stream(request, campaign_id):
    events = AdEvent.objects.filter(
        aggregate_id=str(campaign_id),
        tenant_id=request.user.tenant_id
    ).order_by('-timestamp')[:100]
    
    data = [{
        'event_type': event.event_type,
        'timestamp': event.timestamp,
        'payload': event.payload,
        'sequence_number': event.sequence_number
    } for event in events]
    
    return Response(data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def rebuild_campaign_metrics(request, campaign_id):
    events = AdEvent.objects.filter(
        aggregate_id=str(campaign_id),
        tenant_id=request.user.tenant_id
    ).order_by('sequence_number')
    
    # Recalcular métricas desde eventos
    impressions_count = 0
    clicks_count = 0
    conversions_count = 0
    total_spend = 0
    
    for event in events:
        if event.event_type == 'impression_created':
            impressions_count += 1
            total_spend += float(event.payload.get('cost', 0))
        elif event.event_type == 'click_registered':
            clicks_count += 1
        elif event.event_type == 'conversion_tracked':
            conversions_count += 1
    
    return Response({
        'campaign_id': campaign_id,
        'events_processed': events.count(),
        'rebuilt_metrics': {
            'impressions': impressions_count,
            'clicks': clicks_count,
            'conversions': conversions_count,
            'spend': total_spend
        }
    })