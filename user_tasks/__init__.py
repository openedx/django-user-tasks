"""
Management of user-triggered asynchronous tasks in Django projects.
"""

from django.dispatch import Signal

__version__ = '1.2.0'

default_app_config = 'user_tasks.apps.UserTasksConfig'  # pylint: disable=invalid-name

# This signal is emitted when a user task reaches any final state:
# SUCCEEDED, FAILED, or CANCELED
user_task_stopped = Signal(providing_args=['status'])  # pylint: disable=invalid-name
