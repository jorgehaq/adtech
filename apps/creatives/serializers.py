from rest_framework import serializers
from .models import Creative

class CreativeSerializer(serializers.ModelSerializer):
    tenant_id = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Creative
        fields = '__all__'