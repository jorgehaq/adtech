from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AudienceSegmentViewSet

router = DefaultRouter()
router.register(r'audiences', AudienceSegmentViewSet, basename='audience')

urlpatterns = [
    path('', include(router.urls)),
]