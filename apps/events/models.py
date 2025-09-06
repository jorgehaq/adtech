from django.db import models

class ImpressionEvent(models.Model):
    tenant_id = models.IntegerField(db_index=True)
    campaign = models.ForeignKey('campaigns.Campaign', on_delete=models.CASCADE)
    ad = models.ForeignKey('campaigns.Ad', on_delete=models.CASCADE)
    user_id = models.BigIntegerField()
    cost = models.DecimalField(max_digits=10, decimal_places=4)
    timestamp = models.DateTimeField(auto_now_add=True)

class ClickEvent(models.Model):
    tenant_id = models.IntegerField(db_index=True)
    impression = models.ForeignKey(ImpressionEvent, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

class ConversionEvent(models.Model):
    tenant_id = models.IntegerField(db_index=True)
    click = models.ForeignKey(ClickEvent, on_delete=models.CASCADE)
    conversion_value = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)