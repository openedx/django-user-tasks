"""
URLs for user_tasks.
"""

from rest_framework.routers import SimpleRouter

from user_tasks.views import ArtifactViewSet, StatusViewSet

ROUTER = SimpleRouter()
ROUTER.register(r'artifacts', ArtifactViewSet, basename='usertaskartifact')
ROUTER.register(r'tasks', StatusViewSet, basename='usertaskstatus')

urlpatterns = ROUTER.urls
