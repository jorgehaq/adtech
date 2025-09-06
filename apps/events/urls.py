from django.urls import path
from . import views

urlpatterns = [
    path('impression/', views.create_impression_event, name='create_impression'),
    path('click/', views.create_click_event, name='create_click'),
    path('conversion/', views.create_conversion_event, name='create_conversion'),
    path('stream/<int:campaign_id>/', views.get_event_stream, name='event_stream'),
]