# -*- coding: utf-8 -*-
"""
Django admin configuration for the ``django-user-tasks`` models.
"""

from __future__ import absolute_import, unicode_literals

from django.contrib import admin

from .models import UserTaskArtifact, UserTaskStatus

admin.site.register(UserTaskArtifact)
admin.site.register(UserTaskStatus)
