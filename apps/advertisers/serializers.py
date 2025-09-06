from rest_framework import serializers
from .models import Advertiser, AdvertiserBudget

class AdvertiserSerializer(serializers.ModelSerializer):
    tenant_id = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Advertiser
        fields = '__all__'

class AdvertiserBudgetSerializer(serializers.ModelSerializer):
    tenant_id = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = AdvertiserBudget
        fields = '__all__'