# -*- coding: utf-8 -*-
"""
Celery task abstract base classes.
"""

from __future__ import absolute_import, unicode_literals

import inspect
import logging

from celery import shared_task
from celery.task import Task

from django.utils.timezone import now

from .conf import settings
from .models import UserTaskStatus

LOGGER = logging.getLogger(__name__)


class UserTaskMixin(object):
    """
    Mixin class for user-triggered Celery tasks.

    Subclasses should usually override :py:meth:`generate_name` and
    :py:meth:`calculate_total_steps`.  In order to access the
    :py:attr:`status` property (for calling its
    :py:meth:`~user_tasks.models.UserStatus.increment_completed_steps` and
    :py:meth:`~user_tasks.models.UserStatus.set_state` methods), task
    functions should generally be bound (``bind=True`` in the task decorator)
    and have a ``self`` parameter.

    Additionally, all task functions using a UserTaskMixin subclass must
    provide a ``user_id`` parameter, as either a positional or keyword
    argument.
    """

    @classmethod
    def generate_name(cls, arguments_dict):  # pylint: disable=unused-argument
        """
        Generate a name for the corresponding :py:class:`~user_tasks.models.UserTaskStatus` model instance.

        Should be implemented by each subclass to generate a meaningful name
        from the task parameters.  Defaults to the name of the task function.
        """
        return cls.__name__.split('.')[-1]

    @staticmethod
    def calculate_total_steps(arguments_dict):  # pylint: disable=unused-argument
        """
        Determine from the task's parameters how many total steps the task will perform.

        By default, there is only 1 step (the entire task); to allow for more
        useful progress bars in the UI, override this method to specify a
        meaningful larger number and call ``self.status.increment_completed_steps()``
        periodically during task execution.
        """
        return 1

    @classmethod
    def arguments_as_dict(cls, *args, **kwargs):
        """
        Generate the arguments dictionary provided to :py:meth:`generate_name` and :py:meth:`calculate_total_steps`.

        This makes it possible to fetch arguments by name regardless of
        whether they were passed as positional or keyword arguments.  Unnamed
        positional arguments are provided as a tuple under the key ``pos``.
        """
        all_args = (None, ) + args
        return inspect.getcallargs(cls.run, *all_args, **kwargs)  # pylint: disable=deprecated-method

    @property
    def status(self):
        """
        Get the :py:class:`~user_tasks.models.UserTaskStatus` model instance for this UserTaskMixin.
        """
        task_id = self.request.id
        try:
            return UserTaskStatus.objects.get(task_id=task_id)
        except UserTaskStatus.DoesNotExist:
            # Probably an eager task that skipped the before_task_publish
            # signal.  Create a record for it.
            arguments_dict = self.arguments_as_dict(*self.request.args, **self.request.kwargs)
            name = self.generate_name(arguments_dict)
            task_class = '.'.join([self.__class__.__module__, self.__class__.__name__])
            total_steps = self.calculate_total_steps(arguments_dict)
            user_id = arguments_dict['user_id']
            return UserTaskStatus.objects.create(
                name=name, task_id=task_id, task_class=task_class, total_steps=total_steps, user_id=user_id)


class UserTask(Task, UserTaskMixin):  # pylint: disable=abstract-method
    """
    Abstract base class for user-triggered Celery tasks.

    See :py:class:`UserTaskMixin` for details on how to implement and use
    subclasses.
    """

    abstract = True


@shared_task
def purge_old_user_tasks():
    """
    Delete any UserTaskStatus and UserTaskArtifact records older than ``settings.USER_TASKS_MAX_AGE``.

    Intended to be run as a scheduled task.
    """
    limit = now() - settings.USER_TASKS_MAX_AGE
    # UserTaskArtifacts will also be removed via deletion cascading
    UserTaskStatus.objects.filter(created__lt=limit).delete()
