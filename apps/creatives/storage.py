# apps/creatives/storage.py
from google.cloud import storage

class CreativeStorage:
    def __init__(self):
        self.client = storage.Client()
        self.bucket_name = "adtech-creatives"
        
    def upload_creative(self, file_data, tenant_id, creative_id):
        bucket = self.client.bucket(self.bucket_name)
        blob_name = f"tenant_{tenant_id}/creative_{creative_id}"
        blob = bucket.blob(blob_name)
        
        blob.upload_from_string(file_data)
        blob.make_public()
        
        return blob.public_url
    
    def get_cdn_url(self, tenant_id, creative_id):
        return f"https://storage.googleapis.com/{self.bucket_name}/tenant_{tenant_id}/creative_{creative_id}"