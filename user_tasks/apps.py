# -*- coding: utf-8 -*-
"""
user_tasks Django application initialization.
"""

from __future__ import absolute_import, unicode_literals

from django.apps import AppConfig


class UserTasksConfig(AppConfig):
    """
    Configuration for the user_tasks Django application.
    """

    name = 'user_tasks'
    verbose_name = 'User Tasks'

    def ready(self):
        """
        Register Celery signal handlers.
        """
        import user_tasks.signals  # pylint: disable=unused-import
