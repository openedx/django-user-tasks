"""
URLs for REST API schema generation.
"""

from drf_yasg import openapi
from drf_yasg.views import get_schema_view

from django.contrib import admin
from django.urls import include, path, re_path

from rest_framework import permissions

from user_tasks.urls import urlpatterns as base_patterns

SCHEMA = get_schema_view(
   openapi.Info(
      title="Django User Tasks API",
      default_version='v1',
      description="Django User Tasks API docs",
   ),
   public=False,
   permission_classes=[permissions.AllowAny],
)

# The Swagger/Open API JSON file can be found at http://localhost:8000/?format=openapi
urlpatterns = [
   path('admin/', include(admin.site.urls)),
   re_path(r'^swagger(?P<format>\.json|\.yaml)$', SCHEMA.without_ui(cache_timeout=0), name='schema-json'),
   path('swagger/', SCHEMA.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
] + base_patterns
