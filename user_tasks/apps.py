"""
user_tasks Django application initialization.
"""

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
        import user_tasks.signals  # pylint: disable=unused-variable, import-outside-toplevel, unused-import
