from django.db import models

class Creative(models.Model):
    tenant_id = models.IntegerField(db_index=True)
    name = models.CharField(max_length=100)
    asset_url = models.URLField()
    creative_type = models.CharField(max_length=50)  # banner, video, native
    status = models.CharField(max_length=20, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)