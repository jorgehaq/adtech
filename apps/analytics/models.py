from django.db import models

# Create your models here.
class CampaignMetrics(models.Model):
    tenant_id = models.IntegerField(db_index=True)
    campaign = models.ForeignKey('campaigns.Campaign', on_delete=models.CASCADE)
    date = models.DateField()
    impressions = models.BigIntegerField(default=0)
    clicks = models.BigIntegerField(default=0)
    conversions = models.BigIntegerField(default=0)
    spend = models.DecimalField(max_digits=12, decimal_places=2)


class AdEvent(models.Model):
    tenant_id = models.IntegerField(db_index=True)
    event_type = models.CharField(max_length=50)  # impression, click, conversion
    aggregate_id = models.CharField(max_length=100)  # campaign_id
    payload = models.JSONField()
    timestamp = models.DateTimeField(auto_now_add=True)
    sequence_number = models.BigIntegerField()