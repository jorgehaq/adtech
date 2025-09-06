from django.db import models

class BidRequest(models.Model):
    tenant_id = models.IntegerField(db_index=True)
    request_id = models.CharField(max_length=100, unique=True)
    user_id = models.BigIntegerField()
    placement_id = models.CharField(max_length=100)
    floor_price = models.DecimalField(max_digits=10, decimal_places=4)
    timestamp = models.DateTimeField(auto_now_add=True)

class BidResponse(models.Model):
    tenant_id = models.IntegerField(db_index=True)
    bid_request = models.ForeignKey(BidRequest, on_delete=models.CASCADE)
    campaign = models.ForeignKey('campaigns.Campaign', on_delete=models.CASCADE)
    bid_price = models.DecimalField(max_digits=10, decimal_places=4)
    won = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)