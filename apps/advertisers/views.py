from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Advertiser, AdvertiserBudget
from .serializers import AdvertiserSerializer, AdvertiserBudgetSerializer

class AdvertiserViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = AdvertiserSerializer
    
    def get_queryset(self):
        return Advertiser.objects.filter(tenant_id=self.request.user.tenant_id)
    
    def perform_create(self, serializer):
        serializer.save(tenant_id=self.request.user.tenant_id)

class AdvertiserBudgetViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = AdvertiserBudgetSerializer
    
    def get_queryset(self):
        return AdvertiserBudget.objects.filter(tenant_id=self.request.user.tenant_id)
    
    def perform_create(self, serializer):
        serializer.save(tenant_id=self.request.user.tenant_id)