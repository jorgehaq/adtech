from django.db import models

class Campaign(models.Model):
    tenant_id = models.IntegerField(db_index=True)
    name = models.CharField(max_length=100)
    budget = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20)
    start_date = models.DateField()
    end_date = models.DateField()

class Ad(models.Model):
    tenant_id = models.IntegerField(db_index=True)
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='ads')
    creative_url = models.URLField()
    target_audience = models.CharField(max_length=100)

class Impression(models.Model):
    tenant_id = models.IntegerField(db_index=True)
    ad = models.ForeignKey(Ad, on_delete=models.CASCADE, related_name='impressions')
    user_id = models.BigIntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)
    cost = models.DecimalField(max_digits=10, decimal_places=4)