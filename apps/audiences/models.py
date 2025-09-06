from django.db import models

class AudienceSegment(models.Model):
    tenant_id = models.IntegerField(db_index=True)
    name = models.CharField(max_length=100)
    description = models.TextField()
    criteria = models.JSONField()  # targeting rules
    size = models.BigIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

class UserSegment(models.Model):
    tenant_id = models.IntegerField(db_index=True)
    user_id = models.BigIntegerField()
    segment = models.ForeignKey(AudienceSegment, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)