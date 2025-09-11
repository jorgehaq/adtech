from django.urls import path
from . import views
from apps.events.views import rebuild_campaign_metrics
from apps.analytics.views import AggregateMetricsView

urlpatterns = [
    path('cohorts/', views.cohort_analysis, name='cohort_analysis'),
    path('performance/', views.campaign_performance, name='campaign_performance'),
    path('async/cohorts/', views.async_cohort_analysis, name='async_cohort_analysis'),
    path('async/dashboard/', views.async_dashboard, name='async_dashboard'),
    path('trigger-metrics/', views.trigger_metrics, name='trigger_metrics'),
    path('audit/campaign/<int:campaign_id>/events/', views.audit_trail, name='audit_trail'),
    path('rebuild-metrics/<int:campaign_id>/', rebuild_campaign_metrics, name='rebuild_metrics'),
    path('attribution/', views.attribution_analysis, name='attribution_analysis'),
    path('profiling/', views.query_profiling, name='query_profiling'),
    path('indexes/', views.index_analysis, name='index_analysis'),
    path('benchmark/', views.performance_benchmark, name='performance_benchmark'),
    path('realtime/dashboard/', views.real_time_dashboard, name='realtime_dashboard'),
    path('bid/simulate/', views.bid_processing_simulation, name='bid_simulation'),
    path('realtime/metrics/', views.real_time_metrics, name='realtime_metrics'),
    path('cohorts/advanced/', views.advanced_cohort_analysis, name='advanced_cohorts'),
    path('campaigns/ranking/', views.campaign_performance_ranking, name='campaign_ranking'),
    path('campaigns/<int:campaign_id>/hourly/', views.hourly_performance_trend, name='hourly_trend'),
    path('performance/monitor/', views.query_performance_monitor, name='query_monitor'),
    path('circuit-breaker/status/', views.circuit_breaker_status, name='circuit_status'),
    path('aggregate/', AggregateMetricsView.as_view(), name='aggregate-metrics'),

]