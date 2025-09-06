from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Invoice, Payment
from .serializers import InvoiceSerializer, PaymentSerializer

class InvoiceViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = InvoiceSerializer
    
    def get_queryset(self):
        return Invoice.objects.filter(tenant_id=self.request.user.tenant_id)
    
    def perform_create(self, serializer):
        serializer.save(tenant_id=self.request.user.tenant_id)

class PaymentViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = PaymentSerializer
    
    def get_queryset(self):
        return Payment.objects.filter(tenant_id=self.request.user.tenant_id)
    
    def perform_create(self, serializer):
        serializer.save(tenant_id=self.request.user.tenant_id)