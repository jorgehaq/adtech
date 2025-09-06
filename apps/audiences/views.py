from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import AudienceSegment, UserSegment
from .serializers import AudienceSegmentSerializer

class AudienceSegmentViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = AudienceSegmentSerializer
    
    def get_queryset(self):
        return AudienceSegment.objects.filter(tenant_id=self.request.user.tenant_id)
    
    def perform_create(self, serializer):
        serializer.save(tenant_id=self.request.user.tenant_id)