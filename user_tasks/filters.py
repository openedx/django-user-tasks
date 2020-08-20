#!/usr/bin/env python
"""
Optional Django REST Framework filter backends for the ``django-user-tasks`` REST API.
"""

from rest_framework.filters import BaseFilterBackend


class ArtifactFilterBackend(BaseFilterBackend):
    """
    Default filter for UserTaskArtifact listings in the REST API.

    Ensures that superusers can see all artifacts, but other users
    can only see artifacts for tasks they personally triggered.
    """

    def filter_queryset(self, request, queryset, view):
        """
        Filter out any artifacts which the requesting user does not have permission to view.
        """
        if request.user.is_superuser:
            return queryset
        return queryset.filter(status__user=request.user)


class StatusFilterBackend(BaseFilterBackend):
    """
    Default filter for UserTaskStatus listings in the REST API.

    Ensures that superusers can see all task status records, but other users
    can only see records for tasks they personally triggered.
    """

    def filter_queryset(self, request, queryset, view):
        """
        Filter out any status records which the requesting user does not have permission to view.
        """
        if request.user.is_superuser:
            return queryset
        return queryset.filter(user=request.user)
