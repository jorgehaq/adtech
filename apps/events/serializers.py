from rest_framework import serializers
from .models import ImpressionEvent, ClickEvent, ConversionEvent

class ImpressionEventSerializer(serializers.ModelSerializer):
    tenant_id = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = ImpressionEvent
        fields = '__all__'

class ClickEventSerializer(serializers.ModelSerializer):
    tenant_id = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = ClickEvent
        fields = '__all__'

class ConversionEventSerializer(serializers.ModelSerializer):
    tenant_id = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = ConversionEvent
        fields = '__all__'