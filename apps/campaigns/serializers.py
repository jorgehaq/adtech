from rest_framework import serializers
from .models import Campaign, Ad

class CampaignSerializer(serializers.ModelSerializer):
    tenant_id = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Campaign
        fields = '__all__'
    
    def validate_name(self, value):
        # Get tenant_id from context (set in the view)
        request = self.context.get('request')
        if request and hasattr(request.user, 'tenant_id'):
            tenant_id = request.user.tenant_id
            
            # Check if updating existing campaign
            if self.instance and hasattr(self.instance, 'pk'):
                # For updates, exclude current instance from the check
                existing_campaign = Campaign.objects.filter(
                    tenant_id=tenant_id, 
                    name=value
                ).exclude(pk=self.instance.pk).first()
            else:
                # For new campaigns, check if name already exists for this tenant
                existing_campaign = Campaign.objects.filter(
                    tenant_id=tenant_id, 
                    name=value
                ).first()
            
            if existing_campaign:
                raise serializers.ValidationError(
                    f"A campaign with name '{value}' already exists for this tenant."
                )
        
        return value

class AdSerializer(serializers.ModelSerializer):
    tenant_id = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Ad
        fields = '__all__'