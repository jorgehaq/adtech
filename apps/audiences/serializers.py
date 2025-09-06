from rest_framework import serializers
from .models import AudienceSegment

class AudienceSegmentSerializer(serializers.ModelSerializer):
    tenant_id = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = AudienceSegment
        fields = '__all__'