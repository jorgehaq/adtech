from django.db import models
from django.core.exceptions import ValidationError

class Campaign(models.Model):
    class Meta:
        app_label = 'campaigns'
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
    
    # Status choices
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('stopped', 'Stopped'),
        ('completed', 'Completed')
    ]
    
    tenant_id = models.IntegerField(db_index=True)
    name = models.CharField(max_length=100)
    budget = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    start_date = models.DateField()
    end_date = models.DateField()
    advertiser = models.ForeignKey('advertisers.Advertiser', on_delete=models.CASCADE)
    
    def clean(self):
        if self.start_date >= self.end_date:
            raise ValidationError("start_date must be before end_date")
    
    def can_transition_to(self, new_status):
        """Validate status transitions"""
        valid_transitions = {
            'draft': ['active'],
            'active': ['paused', 'stopped'],
            'paused': ['active', 'stopped'],
            'stopped': [],  # Terminal state
            'completed': []  # Terminal state
        }
        return new_status in valid_transitions.get(self.status, [])
    
    def save(self, *args, **kwargs):
        if self.pk:  # Updating existing
            old_instance = Campaign.objects.get(pk=self.pk)
            if old_instance.status != self.status:
                if not old_instance.can_transition_to(self.status):
                    raise ValidationError(
                        f"Cannot transition from {old_instance.status} to {self.status}"
                    )
        self.clean()
        super().save(*args, **kwargs)

class Ad(models.Model):
    class Meta:
        app_label = 'campaigns'
    
    tenant_id = models.IntegerField(db_index=True)
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='ads')
    creative_url = models.URLField()
    target_audience = models.CharField(max_length=100)
    creative = models.ForeignKey('creatives.Creative', on_delete=models.CASCADE)
    audience = models.ForeignKey('audiences.AudienceSegment', on_delete=models.CASCADE)

class Impression(models.Model):
    class Meta:
        app_label = 'campaigns'
        indexes = [
            models.Index(fields=['tenant_id', 'timestamp']),
        ]
    
    tenant_id = models.IntegerField(db_index=True)
    ad = models.ForeignKey(Ad, on_delete=models.CASCADE, related_name='impressions')
    user_id = models.BigIntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)
    cost = models.DecimalField(max_digits=10, decimal_places=4)