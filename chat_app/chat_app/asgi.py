"""
ASGI config for chat_app project.
"""

import os
import sys
from pathlib import Path

# Directory containing manage.py — where chat/, accounts/, chat_app/ all live
PROJECT_DIR = str(Path(__file__).resolve().parent.parent)
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

# When Render imports this file as 'chat_app.chat_app.asgi', Python caches
# 'chat_app' as a namespace package pointing to the outer directory.
# Clear it so Django can find the real chat_app Django package instead.
_cached = sys.modules.get('chat_app')
if _cached is not None and getattr(_cached, '__file__', None) is None:
    del sys.modules['chat_app']

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chat_app.settings')

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import chat.routing

application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': AuthMiddlewareStack(
        URLRouter(
            chat.routing.websocket_urlpatterns
        )
    ),
})
