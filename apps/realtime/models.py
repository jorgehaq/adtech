from django.db import models

class MetricSnapshot(models.Model):
    tenant_id = models.IntegerField(db_index=True)
    campaign = models.ForeignKey('campaigns.Campaign', on_delete=models.CASCADE)
    impressions = models.BigIntegerField(default=0)
    clicks = models.BigIntegerField(default=0)
    spend = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    timestamp = models.DateTimeField(auto_now_add=True)