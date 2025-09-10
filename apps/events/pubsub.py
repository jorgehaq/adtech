from google.cloud import pubsub_v1
from django.conf import settings
import json

class EventPublisher:
    def __init__(self):
        self.publisher = pubsub_v1.PublisherClient()
        self.project_id = settings.PROJECT_ID
        
    def publish_impression_event(self, tenant_id, event_data):
        topic_path = self.publisher.topic_path(
            self.project_id, 
            f"impressions-tenant-{tenant_id}"
        )
        
        message_data = json.dumps(event_data).encode("utf-8")
        future = self.publisher.publish(topic_path, message_data)
        return future.result()
    
    def publish_click_event(self, tenant_id, event_data):
        topic_path = self.publisher.topic_path(
            self.project_id, 
            f"clicks-tenant-{tenant_id}"
        )
        
        message_data = json.dumps(event_data).encode("utf-8")
        future = self.publisher.publish(topic_path, message_data)
        return future.result()