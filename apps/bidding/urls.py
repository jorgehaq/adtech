from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BidRequestViewSet, BidResponseViewSet

router = DefaultRouter()
router.register(r'bid-requests', BidRequestViewSet, basename='bidrequest')
router.register(r'bid-responses', BidResponseViewSet, basename='bidresponse')

urlpatterns = [
    path('', include(router.urls)),
]