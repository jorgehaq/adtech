from django.db import models

class Advertiser(models.Model):
    tenant_id = models.IntegerField(db_index=True)
    name = models.CharField(max_length=100)
    email = models.EmailField()
    status = models.CharField(max_length=20, default='active')
    created_at = models.DateTimeField(auto_now_add=True)

class AdvertiserBudget(models.Model):
    tenant_id = models.IntegerField(db_index=True)
    advertiser = models.ForeignKey(Advertiser, on_delete=models.CASCADE)
    monthly_budget = models.DecimalField(max_digits=12, decimal_places=2)
    spent = models.DecimalField(max_digits=12, decimal_places=2, default=0)