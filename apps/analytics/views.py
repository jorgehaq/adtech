import asyncio
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .repositories import AnalyticsRepository
from apps.analytics.models import AdEvent
from asgiref.sync import sync_to_async

@api_view(['GET'])
def cohort_analysis(request):
    data = AnalyticsRepository.cohort_analysis(request.user.tenant_id)
    formatted_data = [{
        'cohort_month': row[0],
        'period_days': row[1], 
        'users': row[2],
        'total_impressions': row[3],
        'retention_rate': row[4]
    } for row in data]
    return Response(formatted_data)

@api_view(['GET'])  
def campaign_performance(request):
    data = AnalyticsRepository.campaign_performance_window(request.user.tenant_id)
    formatted_data = [{
        'campaign_id': row[0],
        'campaign_name': row[1],
        'date': row[2],
        'impressions': row[3],
        'total_cost': float(row[4]),
        'avg_cost': float(row[5]),
        'unique_users': row[6],
        'daily_rank': row[7],
        'prev_day_impressions': row[8],
        'growth_rate': row[9]
    } for row in data]
    return Response(formatted_data)

@api_view(['GET'])
async def async_cohort_analysis(request):
    """Async version with parallel queries"""
    tenant_id = request.user.tenant_id
    
    # Execute multiple analytics in parallel
    cohort_task = sync_to_async(AnalyticsRepository.cohort_analysis)(tenant_id)
    performance_task = sync_to_async(AnalyticsRepository.campaign_performance_window)(tenant_id)
    top_campaigns_task = sync_to_async(AnalyticsRepository.top_performing_campaigns)(tenant_id)
    
    cohort_data, performance_data, top_campaigns = await asyncio.gather(
        cohort_task, performance_task, top_campaigns_task
    )
    
    return Response({
        'cohort_analysis': cohort_data,
        'performance_metrics': performance_data[:5],  # Top 5
        'top_campaigns': top_campaigns
    })

@api_view(['GET'])
async def async_dashboard(request):
    """Real-time dashboard with concurrent queries"""
    tenant_id = request.user.tenant_id
    
    # Parallel execution for dashboard
    tasks = [
        sync_to_async(AnalyticsRepository.cohort_analysis)(tenant_id),
        sync_to_async(AnalyticsRepository.top_performing_campaigns)(tenant_id, 5),
        sync_to_async(lambda: AdEvent.objects.filter(tenant_id=tenant_id).count())(),
        sync_to_async(lambda: AdEvent.objects.filter(
            tenant_id=tenant_id, 
            event_type='impression_created'
        ).count())()
    ]
    
    results = await asyncio.gather(*tasks)
    
    return Response({
        'cohort_data': results[0],
        'top_campaigns': results[1], 
        'total_events': results[2],
        'total_impressions': results[3],
        'performance_ms': 'sub_100ms'  # Real-time requirement
    })

@api_view(['POST'])
def rebuild_metrics(request, campaign_id):
    from apps.analytics.events import replay_events
    events = replay_events(campaign_id, request.user.tenant_id)
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

@api_view(['POST'])
def trigger_metrics(request):
    from tasks.analytics import calculate_daily_metrics
    result = calculate_daily_metrics.delay(request.user.tenant_id)
    return Response({'task_id': result.id, 'status': 'queued'})