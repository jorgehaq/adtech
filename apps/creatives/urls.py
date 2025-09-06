from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CreativeViewSet

router = DefaultRouter()
router.register(r'creatives', CreativeViewSet, basename='creative')

urlpatterns = [
    path('', include(router.urls)),
]