# apps/realtime/consumers.py
import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from apps.campaigns.models import Campaign, Impression
from apps.analytics.models import AdEvent

class CampaignMetricsConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.campaign_id = self.scope['url_route']['kwargs']['campaign_id']
        self.tenant_id = self.scope['user'].tenant_id if hasattr(self.scope.get('user'), 'tenant_id') else 1
        self.room_group_name = f'campaign_{self.campaign_id}_metrics'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        
        # Start sending real-time metrics
        asyncio.create_task(self.send_metrics_loop())

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        # Handle incoming messages (if needed)
        pass

    async def send_metrics_loop(self):
        """Send real-time metrics every 2 seconds"""
        while True:
            try:
                metrics = await self.get_campaign_metrics()
                await self.send(text_data=json.dumps({
                    'type': 'metrics_update',
                    'campaign_id': self.campaign_id,
                    'data': metrics,
                    'timestamp': asyncio.get_event_loop().time()
                }))
                await asyncio.sleep(2)  # Update every 2 seconds
            except Exception as e:
                break

    @database_sync_to_async
    def get_campaign_metrics(self):
        """Get real-time campaign metrics"""
        from django.db import connection
        
        sql = """
        SELECT 
            COUNT(*) as impressions,
            COUNT(DISTINCT ci.user_id) as unique_users,
            SUM(ci.cost) as total_spend,
            AVG(ci.cost) as avg_cpm,
            COUNT(*) / NULLIF(COUNT(DISTINCT ci.user_id), 0) as frequency
        FROM campaigns_impression ci
        JOIN campaigns_ad ad ON ci.ad_id = ad.id
        WHERE ad.campaign_id = %s 
        AND ci.tenant_id = %s
        AND ci.timestamp >= NOW() - INTERVAL 1 HOUR
        """
        
        with connection.cursor() as cursor:
            cursor.execute(sql, [self.campaign_id, self.tenant_id])
            row = cursor.fetchone()
            
            return {
                'impressions': row[0] or 0,
                'unique_users': row[1] or 0,
                'total_spend': float(row[2] or 0),
                'avg_cpm': float(row[3] or 0),
                'frequency': float(row[4] or 0),
                'performance_trend': 'up' if (row[0] or 0) > 100 else 'stable'
            }

    # Receive message from room group
    async def metrics_update(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps(event))


# apps/realtime/routing.py
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/campaign/(?P<campaign_id>\w+)/metrics/$', consumers.CampaignMetricsConsumer.as_asgi()),
]