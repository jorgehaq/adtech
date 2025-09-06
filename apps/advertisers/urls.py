from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AdvertiserViewSet, AdvertiserBudgetViewSet

router = DefaultRouter()
router.register(r'advertisers', AdvertiserViewSet, basename='advertiser')
router.register(r'budgets', AdvertiserBudgetViewSet, basename='budget')

urlpatterns = [
    path('', include(router.urls)),
]