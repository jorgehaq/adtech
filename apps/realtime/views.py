from rest_framework.decorators import api_view
from rest_framework.response import Response
from asgiref.sync import sync_to_async
from .pubsub import EventStreamer, RealTimeProcessor

@api_view(['POST'])
def publish_test_events(request):  # ← Quitar async
    """Test endpoint to publish events to stream"""
    import asyncio
    
    async def _publish_async():
        tenant_id = request.user.tenant_id
        campaign_id = request.data.get('campaign_id', 1)
        
        streamer = EventStreamer()
        
        # Publish test impression
        impression_event = await streamer.publish_impression_event(
            tenant_id, 
            campaign_id,
            {
                'user_id': 12345,
                'cost': 0.75,
                'placement': 'homepage_banner'
            }
        )
        
        return {
            'impression_published': impression_event,
            'stream_status': 'active'
        }
    
    # Run async function synchronously
    result = asyncio.run(_publish_async())
    return Response(result)

@api_view(['GET'])
def stream_status(request):  # ← Quitar async
    """Check streaming status and metrics"""
    processor = RealTimeProcessor()
    
    return Response({
        'active_streams': len(processor.metrics_cache),
        'cached_metrics': processor.metrics_cache,
        'redis_connected': processor.streamer.redis_client.ping(),
        'pubsub_simulation': 'active'
    })