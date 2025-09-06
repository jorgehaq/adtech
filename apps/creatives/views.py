from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Creative
from .serializers import CreativeSerializer

class CreativeViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CreativeSerializer
    
    def get_queryset(self):
        return Creative.objects.filter(tenant_id=self.request.user.tenant_id)
    
    def perform_create(self, serializer):
        serializer.save(tenant_id=self.request.user.tenant_id)