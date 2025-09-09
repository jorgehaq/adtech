from django.urls import path
from . import views

urlpatterns = [
    path('publish/', views.publish_test_events, name='publish_events'),
    path('status/', views.stream_status, name='stream_status'),
]