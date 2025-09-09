from django.urls import path
from . import views
from apps.events.views import rebuild_campaign_metrics

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
]