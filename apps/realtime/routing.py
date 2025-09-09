
# apps/realtime/routing.py
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/campaign/(?P<campaign_id>\w+)/metrics/$', consumers.CampaignMetricsConsumer.as_asgi()),
    re_path(r'ws/realtime/dashboard/$', consumers.DashboardConsumer.as_asgi()),
]