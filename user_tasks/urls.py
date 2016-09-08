# -*- coding: utf-8 -*-
"""
URLs for user_tasks.
"""
from __future__ import absolute_import, unicode_literals

from rest_framework.routers import SimpleRouter

from user_tasks.views import ArtifactViewSet, StatusViewSet

ROUTER = SimpleRouter()
ROUTER.register(r'artifacts', ArtifactViewSet, base_name='usertaskartifact')
ROUTER.register(r'tasks', StatusViewSet, base_name='usertaskstatus')

urlpatterns = ROUTER.urls
