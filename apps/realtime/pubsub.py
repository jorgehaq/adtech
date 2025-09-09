import asyncio
import json
import redis
from django.conf import settings

class EventStreamer:
    def __init__(self):
        self.redis_client = redis.Redis(host='127.0.0.1', port=6379, db=3)
        
    async def publish_impression_event(self, tenant_id, campaign_id, event_data):
        """Simulate Pub/Sub impression event publishing"""
        topic = f"impressions.tenant.{tenant_id}"
        
        event = {
            'event_type': 'impression_created',
            'tenant_id': tenant_id,
            'campaign_id': campaign_id,
            'timestamp': asyncio.get_event_loop().time(),
            'data': event_data
        }
        
        # Publish to Redis (simulating Google Pub/Sub)
        self.redis_client.publish(topic, json.dumps(event))
        return event
    
    async def publish_click_event(self, tenant_id, campaign_id, impression_id):
        """Simulate click event streaming"""
        topic = f"clicks.tenant.{tenant_id}"
        
        event = {
            'event_type': 'click_registered',
            'tenant_id': tenant_id,
            'campaign_id': campaign_id,
            'impression_id': impression_id,
            'timestamp': asyncio.get_event_loop().time()
        }
        
        self.redis_client.publish(topic, json.dumps(event))
        return event
    
    async def subscribe_to_events(self, tenant_id, callback):
        """Subscribe to tenant events stream"""
        topics = [f"impressions.tenant.{tenant_id}", f"clicks.tenant.{tenant_id}"]
        pubsub = self.redis_client.pubsub()
        
        for topic in topics:
            pubsub.subscribe(topic)
        
        async for message in pubsub.listen():
            if message['type'] == 'message':
                event_data = json.loads(message['data'])
                await callback(event_data)

# Event processor for real-time analytics
class RealTimeProcessor:
    def __init__(self):
        self.streamer = EventStreamer()
        self.metrics_cache = {}
    
    async def process_event_stream(self, tenant_id):
        """Process incoming events and update metrics"""
        await self.streamer.subscribe_to_events(tenant_id, self.handle_event)
    
    async def handle_event(self, event_data):
        """Handle individual events and update real-time metrics"""
        tenant_id = event_data['tenant_id']
        campaign_id = event_data['campaign_id']
        
        # Update in-memory metrics cache
        cache_key = f"{tenant_id}:{campaign_id}"
        if cache_key not in self.metrics_cache:
            self.metrics_cache[cache_key] = {
                'impressions': 0,
                'clicks': 0,
                'last_update': asyncio.get_event_loop().time()
            }
        
        if event_data['event_type'] == 'impression_created':
            self.metrics_cache[cache_key]['impressions'] += 1
        elif event_data['event_type'] == 'click_registered':
            self.metrics_cache[cache_key]['clicks'] += 1
            
        self.metrics_cache[cache_key]['last_update'] = asyncio.get_event_loop().time()
        
        # Broadcast to WebSocket clients
        await self.broadcast_to_websockets(tenant_id, campaign_id, self.metrics_cache[cache_key])
    
    async def broadcast_to_websockets(self, tenant_id, campaign_id, metrics):
        """Send updated metrics to WebSocket connections"""
        from channels.layers import get_channel_layer
        
        channel_layer = get_channel_layer()
        group_name = f'campaign_{campaign_id}_metrics'
        
        await channel_layer.group_send(
            group_name,
            {
                'type': 'metrics_update',
                'campaign_id': campaign_id,
                'data': metrics
            }
        )
