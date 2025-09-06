from django.db import models

class Campaign(models.Model):
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['tenant_id', 'name'],
                name='unique_campaign_name_per_tenant'
            )
        ]
        indexes = [
            models.Index(fields=['tenant_id', 'status']),
            models.Index(fields=['tenant_id', 'start_date']),
        ]
    
    tenant_id = models.IntegerField(db_index=True)  # Este mantenerlo
    name = models.CharField(max_length=100)
    budget = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20)  # Quitar db_index
    start_date = models.DateField()  # Quitar db_index
    end_date = models.DateField()
    advertiser = models.ForeignKey('advertisers.Advertiser', on_delete=models.CASCADE)

class Ad(models.Model):
    tenant_id = models.IntegerField(db_index=True)
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='ads')
    creative_url = models.URLField()
    target_audience = models.CharField(max_length=100)
    creative = models.ForeignKey('creatives.Creative', on_delete=models.CASCADE)
    audience = models.ForeignKey('audiences.AudienceSegment', on_delete=models.CASCADE)

class Impression(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=['tenant_id', 'timestamp']),
        ]
    
    tenant_id = models.IntegerField(db_index=True)
    ad = models.ForeignKey(Ad, on_delete=models.CASCADE, related_name='impressions')
    user_id = models.BigIntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)
    cost = models.DecimalField(max_digits=10, decimal_places=4)