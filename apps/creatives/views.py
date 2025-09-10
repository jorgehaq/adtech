from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Creative
from .serializers import CreativeSerializer

class CreativeViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CreativeSerializer
    
    def get_queryset(self):
        return Creative.objects.filter(tenant_id=self.request.user.tenant_id)
    
    def perform_create(self, serializer):
        serializer.save(tenant_id=self.request.user.tenant_id)


# apps/creatives/views.py (adicionar)
@api_view(['POST'])
def upload_to_gcs(request):
    from .storage import CreativeStorage
    
    storage = CreativeStorage()
    file_data = request.FILES['creative'].read()
    creative_id = request.data['creative_id']
    
    url = storage.upload_creative(
        file_data, 
        request.user.tenant_id, 
        creative_id
    )
    
    return Response({'cdn_url': url})