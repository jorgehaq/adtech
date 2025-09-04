from rest_framework import serializers
from .models import Campaign, Ad

class CampaignSerializer(serializers.ModelSerializer):
    tenant_id = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Campaign
        fields = '__all__'

class AdSerializer(serializers.ModelSerializer):
    tenant_id = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Ad
        fields = '__all__'