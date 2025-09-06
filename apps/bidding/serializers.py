from rest_framework import serializers
from .models import BidRequest, BidResponse

class BidRequestSerializer(serializers.ModelSerializer):
    tenant_id = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = BidRequest
        fields = '__all__'

class BidResponseSerializer(serializers.ModelSerializer):
    tenant_id = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = BidResponse
        fields = '__all__'