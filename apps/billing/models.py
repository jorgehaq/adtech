from django.db import models

class Invoice(models.Model):
    tenant_id = models.IntegerField(db_index=True)
    advertiser = models.ForeignKey('advertisers.Advertiser', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    period_start = models.DateField()
    period_end = models.DateField()
    status = models.CharField(max_length=20, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

class Payment(models.Model):
    tenant_id = models.IntegerField(db_index=True)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=50)
    processed_at = models.DateTimeField(auto_now_add=True)