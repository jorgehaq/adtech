from rest_framework.decorators import api_view
from rest_framework.response import Response
from .repositories import AnalyticsRepository
from apps.analytics.models import AdEvent

@api_view(['GET'])
def cohort_analysis(request):
    data = AnalyticsRepository.cohort_analysis(request.user.tenant_id)
    return Response(data)

@api_view(['GET'])  
def campaign_performance(request):
    data = AnalyticsRepository.campaign_performance_window(request.user.tenant_id)
    return Response(data)

@api_view(['POST'])
def rebuild_metrics(request, campaign_id):
    events = replay_events(campaign_id, request.user.tenant_id)
    # Recalcular métricas
    return Response({'rebuilt': len(events)})

@api_view(['GET'])
def audit_trail(request, campaign_id):
    events = AdEvent.objects.filter(
        aggregate_id=str(campaign_id),
        tenant_id=request.user.tenant_id
    ).order_by('-timestamp')
    
    data = [{
        'event_type': event.event_type,
        'timestamp': event.timestamp,
        'payload': event.payload,
        'sequence_number': event.sequence_number
    } for event in events]
    
    return Response(data)



from asgiref.sync import sync_to_async

@api_view(['GET'])
async def async_analytics(request):
    data = await sync_to_async(AnalyticsRepository.cohort_analysis)(request.user.tenant_id)
    return Response(data)

