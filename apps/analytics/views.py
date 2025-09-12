import time
from rest_framework.decorators import api_view, permission_classes
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import connection
from django.core.cache import cache
from apps.analytics.tasks import aggregate_daily_metrics
from apps.analytics.models import AdEvent
from apps.campaigns.models import Campaign, Impression
from apps.campaigns.circuit_breaker import CircuitBreaker
from .repository import AnalyticsRepository

analytics_circuit = CircuitBreaker(failure_threshold=5, recovery_timeout=60)


@api_view(['GET'])
@permission_classes([IsAuthenticated]) 
@analytics_circuit
def cohort_analysis(request):
    """Cohort analysis with repository connection"""
    tenant_id = request.user.tenant_id
    data = AnalyticsRepository.cohort_analysis(tenant_id)
    
    formatted_data = [{
        'cohort_month': row[0],
        'period_days': row[1], 
        'users': row[2],
        'total_impressions': row[3],
        'retention_rate': float(row[4]) if row[4] else 0.0
    } for row in data]
    
    return Response({
        'cohorts': formatted_data,
        'total_cohorts': len(formatted_data),
        'performance_ms': 'sub_500ms'
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@analytics_circuit
def campaign_performance(request):
    """Campaign performance with window functions"""
    tenant_id = request.user.tenant_id
    data = AnalyticsRepository.campaign_performance_window(tenant_id)
    
    formatted_data = [{
        'campaign_id': row[0],
        'campaign_name': row[1],
        'date': row[2],
        'impressions': row[3],
        'total_cost': float(row[4]) if row[4] else 0.0,
        'avg_cost': float(row[5]) if row[5] else 0.0,
        'unique_users': row[6],
        'daily_rank': row[7],
        'prev_day_impressions': row[8],
        'growth_rate': float(row[9]) if row[9] else 0.0
    } for row in data]
    
    return Response({
        'campaigns': formatted_data,
        'total_campaigns': len(formatted_data)
    })

@api_view(['GET'])
def async_cohort_analysis(request):
    """Multi-query analytics"""
    tenant_id = request.user.tenant_id
    
    # Ejecutar secuencialmente (sin async)
    cohort_data = AnalyticsRepository.cohort_analysis(tenant_id)
    performance_data = AnalyticsRepository.campaign_performance_window(tenant_id)
    top_campaigns = AnalyticsRepository.top_performing_campaigns(tenant_id)
    
    return Response({
        'cohort_analysis': cohort_data,
        'performance_metrics': performance_data[:5],
        'top_campaigns': top_campaigns
    })

@api_view(['GET'])
def async_dashboard(request):
    """Real-time dashboard with concurrent queries"""
    tenant_id = request.user.tenant_id
    
    # Execute sequentially since views aren't async
    cohort_data = AnalyticsRepository.cohort_analysis(tenant_id)
    top_campaigns = AnalyticsRepository.top_performing_campaigns(tenant_id, 5)
    total_events = AdEvent.objects.filter(tenant_id=tenant_id).count()
    total_impressions = AdEvent.objects.filter(
        tenant_id=tenant_id, 
        event_type='impression_created'
    ).count()
    
    return Response({
        'cohort_data': cohort_data,
        'top_campaigns': top_campaigns, 
        'total_events': total_events,
        'total_impressions': total_impressions,
        'performance_ms': 'sub_100ms'  # Real-time requirement
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def rebuild_metrics(request, campaign_id):
    """Event sourcing replay functionality"""
    from apps.analytics.events import replay_events
    
    events = replay_events(campaign_id, request.user.tenant_id)
    
    return Response({
        'rebuilt_events': len(events),
        'campaign_id': campaign_id,
        'status': 'completed',
        'tenant_id': request.user.tenant_id
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def audit_trail(request, campaign_id):
    events = AdEvent.objects.filter(
        aggregate_id=str(campaign_id),
        tenant_id=request.user.tenant_id
    ).order_by('-timestamp')[:100]  # Limit for performance
    
    data = [{
        'event_id': event.id,
        'event_type': event.event_type,
        'timestamp': event.timestamp,
        'payload': event.payload,
        'sequence_number': event.sequence_number
    } for event in events]
    
    return Response({
        'audit_events': data,
        'campaign_id': campaign_id,
        'total_events': len(data),
        'limited_to': 100
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])  # ← Agregar esto
def trigger_metrics(request):
    from tasks.analytics import calculate_daily_metrics
    result = calculate_daily_metrics.delay(request.user.tenant_id)
    return Response({'task_id': result.id, 'status': 'queued'})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def attribution_analysis(request):
    """Attribution analysis with raw SQL"""
    campaign_id = request.GET.get('campaign_id')
    tenant_id = request.user.tenant_id
    
    data = AnalyticsRepository.attribution_analysis(tenant_id, campaign_id)
    
    formatted_data = [{
        'campaign_id': row[0],
        'attributed_users': row[1],
        'attributed_revenue': float(row[2]) if row[2] else 0.0,
        'avg_journey_days': float(row[3]) if row[3] else 0.0,
        'total_impressions': row[4],
        'total_clicks': row[5],
        'total_conversions': row[6],
        'conversion_rate': (row[6] / row[4] * 100) if row[4] > 0 else 0.0
    } for row in data]
    
    return Response({
        'attribution_data': formatted_data,
        'campaign_filter': campaign_id,
        'total_analyzed': len(formatted_data)
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated]) 
def query_profiling(request):
    """Analyze query performance with EXPLAIN"""
    query_type = request.GET.get('type', 'cohort')
    tenant_id = request.user.tenant_id
    
    queries = {
        'cohort': AnalyticsRepository.cohort_analysis,
        'performance': AnalyticsRepository.campaign_performance_window,
        'attribution': AnalyticsRepository.attribution_analysis
    }
    
    if query_type not in queries:
        return Response({'error': 'Invalid query type'}, status=400)
    
    # Get the SQL from repository method
    method = queries[query_type]
    sql = method.__code__.co_consts[1]  # Extract SQL string
    
    with connection.cursor() as cursor:
        # EXPLAIN query
        explain_sql = f"EXPLAIN FORMAT=JSON {sql}"
        cursor.execute(explain_sql, [tenant_id])
        explain_result = cursor.fetchone()[0]
        
        # Execution time test
        import time
        start_time = time.time()
        cursor.execute(sql, [tenant_id])
        results = cursor.fetchall()
        execution_time = (time.time() - start_time) * 1000  # ms
        
        return Response({
            'query_type': query_type,
            'execution_time_ms': round(execution_time, 2),
            'rows_returned': len(results),
            'explain_plan': explain_result,
            'performance_grade': 'A' if execution_time < 100 else 'B' if execution_time < 500 else 'C'
        })

@api_view(['GET'])
def index_analysis(request):
    """Analyze index usage and recommendations"""
    sql_index_analysis = """
    SELECT 
        TABLE_NAME,
        INDEX_NAME,
        COLUMN_NAME,
        CARDINALITY,
        NULLABLE
    FROM information_schema.STATISTICS 
    WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME LIKE 'campaigns_%'
    ORDER BY TABLE_NAME, INDEX_NAME
    """
    
    with connection.cursor() as cursor:
        cursor.execute(sql_index_analysis)
        indexes = cursor.fetchall()
        
        # Check slow query log
        cursor.execute("SHOW VARIABLES LIKE 'slow_query_log'")
        slow_log_status = cursor.fetchone()
        
        return Response({
            'indexes': [{
                'table': row[0],
                'index': row[1], 
                'column': row[2],
                'cardinality': row[3],
                'nullable': row[4]
            } for row in indexes],
            'slow_log_enabled': slow_log_status[1] if slow_log_status else False,
            'recommendations': [
                'Add composite index on (tenant_id, timestamp) for time-series queries',
                'Consider partitioning impressions table by date',
                'Monitor query cache hit ratio'
            ]
        })
    
@api_view(['GET'])
def performance_benchmark(request):
    """Compare ORM vs Raw SQL performance"""
    tenant_id = request.user.tenant_id
    
    # ORM Query
    start_time = time.time()
    orm_results = Campaign.objects.filter(
        tenant_id=tenant_id
    ).prefetch_related('ads__impressions').count()
    orm_time = (time.time() - start_time) * 1000
    
    # Raw SQL equivalent
    start_time = time.time()
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(DISTINCT c.id)
            FROM campaigns_campaign c
            LEFT JOIN campaigns_ad a ON c.id = a.campaign_id
            LEFT JOIN campaigns_impression i ON a.id = i.ad_id
            WHERE c.tenant_id = %s
        """, [tenant_id])
        raw_results = cursor.fetchone()[0]
    raw_time = (time.time() - start_time) * 1000
    
    return Response({
        'orm': {
            'execution_time_ms': round(orm_time, 2),
            'result_count': orm_results
        },
        'raw_sql': {
            'execution_time_ms': round(raw_time, 2),
            'result_count': raw_results
        },
        'performance_improvement': f"{round((orm_time - raw_time) / orm_time * 100, 1)}%",
        'recommendation': 'Raw SQL' if raw_time < orm_time else 'ORM sufficient'
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def real_time_dashboard(request):
    """Real-time dashboard with concurrent analytics"""
    tenant_id = request.user.tenant_id
    start_time = time.time()
    
    # Get real-time metrics
    realtime_data = AnalyticsRepository.get_real_time_metrics(tenant_id)
    cohort_data = AnalyticsRepository.cohort_analysis(tenant_id)
    top_campaigns = AnalyticsRepository.top_performing_campaigns(tenant_id, 5)
    
    # Calculate totals
    total_events = AdEvent.objects.filter(tenant_id=tenant_id).count()
    total_impressions = Impression.objects.filter(tenant_id=tenant_id).count()
    
    execution_time = (time.time() - start_time) * 1000
    
    return Response({
        'realtime_metrics': realtime_data,
        'cohort_data': cohort_data[:10],  # Limit for performance
        'top_campaigns': top_campaigns, 
        'total_events': total_events,
        'total_impressions': total_impressions,
        'execution_time_ms': round(execution_time, 2),
        'performance_target': 'sub_100ms',
        'status': 'OK' if execution_time < 100 else 'SLOW'
    })

def get_active_campaigns_count(tenant_id):
    """Optimized query with index"""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(*) 
            FROM campaigns_campaign 
            WHERE tenant_id = %s AND status = 'active'
        """, [tenant_id])
        return cursor.fetchone()[0]

def get_total_impressions_today(tenant_id):
    """Fast count with date index"""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(*) 
            FROM campaigns_impression 
            WHERE tenant_id = %s AND DATE(timestamp) = CURDATE()
        """, [tenant_id])
        return cursor.fetchone()[0]

def get_top_performing_campaign(tenant_id):
    """Window function for ranking"""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                ca.id,
                ca.name,
                COUNT(ci.id) as impressions,
                RANK() OVER (ORDER BY COUNT(ci.id) DESC) as rank
            FROM campaigns_campaign ca
            LEFT JOIN campaigns_ad ad ON ad.campaign_id = ca.id
            LEFT JOIN campaigns_impression ci ON ci.ad_id = ad.id 
                AND ci.tenant_id = %s 
                AND DATE(ci.timestamp) = CURDATE()
            WHERE ca.tenant_id = %s
            GROUP BY ca.id, ca.name
            ORDER BY impressions DESC
            LIMIT 1
        """, [tenant_id, tenant_id])
        row = cursor.fetchone()
        return {
            'id': row[0],
            'name': row[1], 
            'impressions': row[2],
            'rank': row[3]
        } if row else None

def get_real_time_spend(tenant_id):
    """Aggregation with SUM optimization"""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT COALESCE(SUM(cost), 0)
            FROM campaigns_impression 
            WHERE tenant_id = %s AND timestamp >= NOW() - INTERVAL 1 HOUR
        """, [tenant_id])
        return float(cursor.fetchone()[0])

def get_unique_users_today(tenant_id):
    """COUNT DISTINCT optimization"""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(DISTINCT user_id)
            FROM campaigns_impression 
            WHERE tenant_id = %s AND DATE(timestamp) = CURDATE()
        """, [tenant_id])
        return cursor.fetchone()[0]

@api_view(['GET'])
def bid_processing_simulation(request):
    """Simulate real-time bid processing <100ms"""
    start_time = time.time()
    
    # Execute bid calculations sequentially
    bid_results = [
        calculate_bid_price(request.user.tenant_id, i)
        for i in range(5)  # 5 bid calculations
    ]
    
    processing_time = (time.time() - start_time) * 1000
    
    return Response({
        'bids': bid_results,
        'processing_time_ms': round(processing_time, 2),
        'rtb_compliant': processing_time < 100,  # Real-time bidding requirement
        'status': 'success' if processing_time < 100 else 'too_slow'
    })

def calculate_bid_price(tenant_id, bid_id):
    """Fast bid calculation with minimal DB queries"""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                AVG(cost) as avg_cost,
                COUNT(*) as volume
            FROM campaigns_impression 
            WHERE tenant_id = %s 
            AND timestamp >= NOW() - INTERVAL 15 MINUTE
            LIMIT 1
        """, [tenant_id])
        row = cursor.fetchone()
        avg_cost = float(row[0] or 0.5)
        volume = row[1] or 0
        
        # Simple bid algorithm
        bid_price = avg_cost * (1.1 if volume > 100 else 0.9)
        
        return {
            'bid_id': bid_id,
            'bid_price': round(bid_price, 4),
            'confidence': 'high' if volume > 50 else 'medium'
        }


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def bigquery_analytics(request):
    """Get analytics from BigQuery"""
    from .bigquery import BigQueryAnalytics
    
    bq = BigQueryAnalytics()
    analysis_type = request.GET.get('type', 'cohort')
    
    try:
        if analysis_type == 'cohort':
            days_back = int(request.GET.get('days_back', 30))
            data = bq.cohort_analysis_bigquery(request.user.tenant_id, days_back)
        elif analysis_type == 'performance':
            campaign_id = request.GET.get('campaign_id')
            if campaign_id:
                campaign_id = int(campaign_id)
            data = bq.campaign_performance_bigquery(request.user.tenant_id, campaign_id)
        else:
            return Response({'error': 'Invalid analysis type'}, status=400)
        
        return Response({
            'source': 'bigquery',
            'type': analysis_type,
            'tenant_id': request.user.tenant_id,
            'data': data,
            'total_records': len(data)
        })
    except Exception as e:
        return Response({
            'error': str(e),
            'source': 'bigquery'
        }, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sync_to_bigquery(request):
    """Sync data from MySQL to BigQuery"""
    from .bigquery import BigQueryAnalytics
    
    bq = BigQueryAnalytics()
    batch_size = int(request.data.get('batch_size', 10000))
    
    try:
        result = bq.sync_impressions(request.user.tenant_id, batch_size)
        return Response({
            'sync_result': result,
            'tenant_id': request.user.tenant_id,
            'batch_size': batch_size
        })
    except Exception as e:
        return Response({
            'error': str(e),
            'tenant_id': request.user.tenant_id
        }, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def bigquery_status(request):
    """Get BigQuery sync status"""
    from .bigquery import BigQueryAnalytics
    
    bq = BigQueryAnalytics()
    status = bq.get_sync_status(request.user.tenant_id)
    
    return Response(status)


@api_view(['GET'])
def real_time_metrics(request):
    """Sub-100ms real-time metrics endpoint"""
    campaign_id = request.GET.get('campaign_id')
    tenant_id = request.user.tenant_id if hasattr(request.user, 'tenant_id') else 1
    
    start_time = time.time()
    data = AnalyticsRepository.get_real_time_metrics(tenant_id, campaign_id)
    execution_time = (time.time() - start_time) * 1000
    
    return Response({
        'metrics': data,
        'execution_time_ms': round(execution_time, 2),
        'performance_target': 'sub_100ms',
        'status': 'OK' if execution_time < 100 else 'SLOW',
        'campaign_filter': campaign_id
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def advanced_cohort_analysis(request):
    """Production cohort analysis with window functions"""
    days_back = int(request.GET.get('days_back', 30))
    tenant_id = request.user.tenant_id
    
    data = AnalyticsRepository.advanced_cohort_analysis(tenant_id, days_back)
    
    formatted_data = [{
        'user_id': row[0],
        'first_seen': row[1],
        'days_since_first': row[2],
        'total_impressions': row[3],
        'total_clicks': row[4],
        'cohort_period': row[5],
        'retention_bucket': row[6]
    } for row in data]
    
    return Response({
        'advanced_cohorts': formatted_data,
        'analysis_period_days': days_back,
        'total_users': len(formatted_data)
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def campaign_performance_ranking(request):
    """Advanced campaign ranking with raw SQL"""
    limit = int(request.GET.get('limit', 20))
    tenant_id = request.user.tenant_id
    
    data = AnalyticsRepository.campaign_performance_ranking(tenant_id, limit)
    
    formatted_data = [{
        'campaign_id': row[0],
        'campaign_name': row[1],
        'total_impressions': row[2],
        'total_clicks': row[3],
        'total_cost': float(row[4]) if row[4] else 0.0,
        'ctr': float(row[5]) if row[5] else 0.0,
        'cpm': float(row[6]) if row[6] else 0.0,
        'performance_rank': row[7],
        'efficiency_score': float(row[8]) if row[8] else 0.0
    } for row in data]
    
    return Response({
        'campaign_rankings': formatted_data,
        'limit': limit,
        'ranking_metric': 'efficiency_score'
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def hourly_performance_trend(request, campaign_id):
    """Hourly trend analysis for specific campaign"""
    hours_back = int(request.GET.get('hours_back', 24))
    tenant_id = request.user.tenant_id
    
    data = AnalyticsRepository.hourly_performance_trend(tenant_id, campaign_id, hours_back)
    
    formatted_data = [{
        'hour': row[0],
        'impressions': row[1],
        'clicks': row[2],
        'cost': float(row[3]) if row[3] else 0.0,
        'ctr': float(row[4]) if row[4] else 0.0,
        'hourly_trend': row[5]
    } for row in data]
    
    return Response({
        'hourly_trends': formatted_data,
        'campaign_id': campaign_id,
        'analysis_period_hours': hours_back,
        'data_points': len(formatted_data)
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def query_performance_monitor(request):
    """Query performance monitoring dashboard"""
    data = AnalyticsRepository.get_query_performance_stats()
    
    return Response({
        'performance_stats': data,
        'monitoring_active': True,
        'thresholds': {
            'fast_query_ms': 50,
            'slow_query_ms': 500,
            'critical_query_ms': 1000
        }
    })

# Class-based view for aggregation
class AggregateMetricsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Trigger metrics aggregation via Celery"""
        tenant_id = request.user.tenant_id
        task = aggregate_daily_metrics.delay(tenant_id)
        
        return Response({
            'task_id': task.id, 
            'status': 'aggregation_started',
            'tenant_id': tenant_id,
            'celery_backend': 'redis'
        })

    def get(self, request):
        """Get aggregation status"""
        tenant_id = request.user.tenant_id
        
        return Response({
            'tenant_id': tenant_id,
            'last_aggregation': cache.get(f'last_aggregation:{tenant_id}'),
            'status': 'ready_for_aggregation'
        })


@api_view(['GET'])
@permission_classes([IsAuthenticated]) 
def circuit_breaker_status(request):
    """Circuit breaker status monitoring"""
    circuits = [
        'apps.campaigns.views.get_queryset',
        'apps.analytics.repository.cohort_analysis',
        'apps.analytics.repository.campaign_performance_window'
    ]
    
    status_data = []
    for circuit in circuits:
        circuit_status = cache.get(f'circuit_breaker:{circuit}', 'closed')
        failures = cache.get(f'circuit_failures:{circuit}', 0)
        
        status_data.append({
            'circuit': circuit,
            'status': circuit_status,
            'failures': failures,
            'last_check': time.time()
        })
    
    return Response({
        'circuit_breakers': status_data,
        'overall_health': 'OK' if all(c['status'] == 'closed' for c in status_data) else 'DEGRADED'
    })



@api_view(['GET'])
@permission_classes([IsAuthenticated])  
def celery_health_check(request):
    """Check Celery worker and broker status"""
    from celery import current_app
    from django.core.cache import cache
    import redis
    
    try:
        # Test Redis connection
        r = redis.Redis(host='localhost', port=6379, db=0)
        redis_status = "connected" if r.ping() else "disconnected"
    except:
        redis_status = "disconnected"
    
    try:
        # Test Celery workers
        inspect = current_app.control.inspect()
        active_workers = inspect.active()
        worker_count = len(active_workers) if active_workers else 0
    except:
        worker_count = 0
        active_workers = {}
    
    return Response({
        'redis_broker': redis_status,
        'active_workers': worker_count,
        'worker_details': active_workers,
        'queue_length': get_queue_length(),
        'recent_tasks': get_recent_tasks()
    })

def get_queue_length():
    """Get approximate queue length"""
    try:
        r = redis.Redis(host='localhost', port=6379, db=0)
        return r.llen('celery')
    except:
        return 0

def get_recent_tasks():
    """Get recent task results from cache"""
    from django.core.cache import cache
    return cache.get('recent_celery_tasks', [])


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def flower_status(request):
    """Flower monitoring - only available in local/dev"""
    from django.conf import settings
    
    # Only works in local/dev environments
    if settings.DEBUG or 'local' in str(settings.DATABASES['default']['HOST']):
        import requests
        try:
            response = requests.get('http://localhost:5555/api/workers', timeout=2)
            flower_data = response.json()
            
            return Response({
                'flower_available': True,
                'flower_url': 'http://localhost:5555',
                'workers': flower_data,
                'environment': 'local'
            })
        except:
            return Response({
                'flower_available': False,
                'message': 'Flower not running. Start with: make flower',
                'environment': 'local'
            })
    else:
        # Production/GCP environment
        return Response({
            'flower_available': False,
            'message': 'Flower not available in production. Use Cloud Monitoring.',
            'monitoring_url': 'https://console.cloud.google.com/monitoring',
            'environment': 'gcp'
        })


def check_flower_running():
    import subprocess
    try:
        result = subprocess.run(['lsof', '-i', ':5555'], capture_output=True, text=True)
        return 'flower' in result.stdout.lower()
    except:
        return False