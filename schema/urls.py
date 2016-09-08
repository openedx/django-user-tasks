# -*- coding: utf-8 -*-
"""
URLs for REST API schema generation.
"""
from __future__ import absolute_import, unicode_literals

from django.conf.urls import include, url
from django.contrib import admin

from user_tasks.urls import urlpatterns as base_patterns

from .views import swagger

# The Swagger/Open API JSON file can be found at http://localhost:8000/?format=openapi
urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url('^$', swagger),
] + base_patterns
