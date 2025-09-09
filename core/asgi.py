"""
ASGI config for core project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import apps.realtime.routing

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

application = ProtocolTypeRouter({  # ← Maneja múltiples protocolos
    "http": get_asgi_application(),    # ← HTTP requests normales
    "websocket": AuthMiddlewareStack(  # ← WebSocket connections
        URLRouter(
            apps.realtime.routing.websocket_urlpatterns
        )
    ),
})