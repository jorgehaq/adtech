"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path
from django.urls import include
from django.http import JsonResponse
from strawberry.django.views import GraphQLView
from core.graphql.schema import schema
from django.views.decorators.csrf import csrf_exempt
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from apps.analytics.views import bigquery_analytics, sync_to_bigquery
from apps.creatives.views import upload_to_gcs

def home_view(request):
    return JsonResponse({
        "message": "AdTech Backend API",
        "status": "running",
        "endpoints": {
            "admin": "/admin/",
            "api": "/api/v1/",
            "graphql": "/graphql/",
            "docs": "/api/docs/",
            "schema": "/api/schema/"
        }
    })


urlpatterns = [
    path("", home_view, name="home"),
    path("admin/", admin.site.urls),
    path("api/v1/auth/", include("apps.authentication.urls")),
    path("api/v1/analytics/", include("apps.analytics.urls")),
    path("api/v1/events/", include("apps.events.urls")),
    path("api/v1/", include("apps.advertisers.urls")),
    path("api/v1/", include("apps.creatives.urls")),
    path("api/v1/", include("apps.audiences.urls")),
    path("api/v1/", include("apps.bidding.urls")),
    path("api/v1/", include("apps.billing.urls")),
    path("api/v1/realtime/", include("apps.realtime.urls")),
    path("api/v1/", include("apps.campaigns.urls")),
    path('graphql/', GraphQLView.as_view(schema=schema, graphiql=True)),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path('api/v1/analytics/bigquery/', bigquery_analytics),
    path('api/v1/analytics/sync-bigquery/', sync_to_bigquery),
    path('api/v1/creatives/upload-gcs/', upload_to_gcs),
]