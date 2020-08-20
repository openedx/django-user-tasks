"""
URLs for user_tasks.
"""

from rest_framework.routers import SimpleRouter

from user_tasks.views import ArtifactViewSet, StatusViewSet

ROUTER = SimpleRouter()
ROUTER.register(r'artifacts', ArtifactViewSet, base_name='usertaskartifact')
ROUTER.register(r'tasks', StatusViewSet, base_name='usertaskstatus')

urlpatterns = ROUTER.urls
