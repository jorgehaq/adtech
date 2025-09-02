from rest_framework import viewsets
from .models import Campaign, Ad
from .serializers import CampaignSerializer, AdSerializer

class CampaignViewSet(viewsets.ModelViewSet):
    queryset = Campaign.objects.all()
    serializer_class = CampaignSerializer

    def create(self, request, *args, **kwargs):
        # Ejemplo de error controlado
        if request.data.get("budget") == "0":  # example condition
            raise ValidationError("Presupuesto no puede ser cero")
        return super().create(request, *args, **kwargs)

    def get_object(self):
        try:
            return super().get_object()
        except Exception:
            raise NotFound("Campaña no encontrada")

class AdViewSet(viewsets.ModelViewSet):
    queryset = Ad.objects.all()
    serializer_class = AdSerializer