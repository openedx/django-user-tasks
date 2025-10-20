"""
Management of user-triggered asynchronous tasks in Django projects.
"""

from django.dispatch import Signal

__version__ = '3.4.4'


# This signal is emitted when a user task reaches any final state:
# SUCCEEDED, FAILED, or CANCELED
# providing_args = ['status']
user_task_stopped = Signal()
