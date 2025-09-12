from django.urls import path
from . import views

urlpatterns = [
    # Event recording endpoints
    path('impression/', views.record_impression, name='record_impression'),
    path('click/', views.record_click, name='record_click'), 
    path('conversion/', views.record_conversion, name='record_conversion'),
    
    # Event sourcing replay
    path('rebuild-metrics/<int:campaign_id>/', views.rebuild_campaign_metrics, name='rebuild_metrics'),
    
    # Event streaming and monitoring
    path('stream/<int:campaign_id>/', views.event_stream, name='event_stream'),
    path('validate/<int:campaign_id>/', views.validate_events, name='validate_events'),
    
    # Event statistics and management
    path('stats/', views.event_stats, name='event_stats'),
    path('cleanup/', views.cleanup_events, name='cleanup_events'),
]