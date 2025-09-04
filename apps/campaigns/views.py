from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Campaign, Ad
from .serializers import CampaignSerializer, AdSerializer

class CampaignViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CampaignSerializer
    queryset = Campaign.objects.all() 

    def get_queryset(self):
        return Campaign.objects.filter(tenant_id=self.request.user.tenant_id)

    def perform_create(self, serializer):
        serializer.save(tenant_id=self.request.user.tenant_id)

class AdViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = AdSerializer
    queryset = Ad.objects.all() 

    def get_queryset(self):
        return Ad.objects.filter(tenant_id=self.request.user.tenant_id)

    def perform_create(self, serializer):
        serializer.save(tenant_id=self.request.user.tenant_id)