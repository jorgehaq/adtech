from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import BidRequest, BidResponse
from .serializers import BidRequestSerializer, BidResponseSerializer

class BidRequestViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = BidRequestSerializer
    
    def get_queryset(self):
        return BidRequest.objects.filter(tenant_id=self.request.user.tenant_id)
    
    def perform_create(self, serializer):
        serializer.save(tenant_id=self.request.user.tenant_id)

class BidResponseViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = BidResponseSerializer
    
    def get_queryset(self):
        return BidResponse.objects.filter(tenant_id=self.request.user.tenant_id)
    
    def perform_create(self, serializer):
        serializer.save(tenant_id=self.request.user.tenant_id)