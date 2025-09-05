from django.urls import path
from . import views

urlpatterns = [
   path('cohorts/', views.cohort_analysis, name='cohort_analysis'),
   path('performance/', views.campaign_performance, name='campaign_performance'),
   path('audit/campaign/<int:campaign_id>/events/', views.audit_trail, name='audit_trail'),  # Agregar esta línea
]