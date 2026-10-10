"""
Management of user-triggered asynchronous tasks in Django projects.
"""

from importlib.metadata import version

from django.dispatch import Signal

__version__ = version("django-user-tasks")


# This signal is emitted when a user task reaches any final state:
# SUCCEEDED, FAILED, or CANCELED
# providing_args = ['status']
user_task_stopped = Signal()
