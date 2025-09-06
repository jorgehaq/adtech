from django.urls import path
from . import views
from apps.events.views import rebuild_campaign_metrics

urlpatterns = [
    path('cohorts/', views.cohort_analysis, name='cohort_analysis'),
    path('performance/', views.campaign_performance, name='campaign_performance'),
    path('audit/campaign/<int:campaign_id>/events/', views.audit_trail, name='audit_trail'),
    path('rebuild-metrics/<int:campaign_id>/', rebuild_campaign_metrics, name='rebuild_metrics'),
]