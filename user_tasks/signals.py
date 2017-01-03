# -*- coding: utf-8 -*-
"""
Celery signal handlers and custom Django signal.
"""

from __future__ import absolute_import, unicode_literals

import logging
from uuid import uuid4

from celery.signals import before_task_publish, task_failure, task_prerun, task_retry, task_success

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils.module_loading import import_string

from user_tasks import user_task_stopped
from .exceptions import TaskCanceledException
from .models import UserTaskStatus
from .tasks import UserTaskMixin

LOGGER = logging.getLogger(__name__)


@before_task_publish.connect
def create_user_task(sender=None, body=None, **kwargs):  # pylint: disable=unused-argument
    """
    Create a :py:class:`UserTaskStatus` record for each :py:class:`UserTaskMixin`.

    Also creates a :py:class:`UserTaskStatus` for each chain, chord, or group containing
    the new :py:class:`UserTaskMixin`.
    """
    try:
        task_class = import_string(sender)
    except ImportError:
        return
    if issubclass(task_class.__class__, UserTaskMixin):
        arguments_dict = task_class.arguments_as_dict(*body['args'], **body['kwargs'])
        user_id = _get_user_id(arguments_dict)
        task_id = body['id']
        if body.get('callbacks', []):
            return _create_chain_entry(user_id, task_id, task_class, body['args'], body['kwargs'], body['callbacks'])
        if body.get('chord', None):
            return _create_chord_entry(task_id, task_class, body, user_id)
        parent = _get_or_create_group_parent(body, user_id)
        name = task_class.generate_name(arguments_dict)
        total_steps = task_class.calculate_total_steps(arguments_dict)
        UserTaskStatus.objects.get_or_create(
            task_id=task_id, defaults={'user_id': user_id, 'parent': parent, 'name': name, 'task_class': sender,
                                       'total_steps': total_steps})
        if parent:
            parent.increment_total_steps(total_steps)


def _create_chain_entry(user_id, task_id, task_class, args, kwargs, callbacks, parent=None):
    """
    Create and update status records for a new :py:class:`UserTaskMixin` in a Celery chain.
    """
    LOGGER.debug(task_class)
    if issubclass(task_class.__class__, UserTaskMixin):
        arguments_dict = task_class.arguments_as_dict(*args, **kwargs)
        name = task_class.generate_name(arguments_dict)
        total_steps = task_class.calculate_total_steps(arguments_dict)
        parent_name = kwargs.get('user_task_name', '')
        with transaction.atomic():
            if parent is None:
                # First task in the chain, create a status record for it
                parent = UserTaskStatus.objects.create(
                    is_container=True, name=parent_name, task_class='celery.chain', task_id=str(uuid4()),
                    total_steps=0, user_id=user_id)
            UserTaskStatus.objects.create(
                name=name, parent=parent, task_class=task_class, task_id=task_id, total_steps=total_steps,
                user_id=user_id)
            parent.increment_total_steps(total_steps)
            if parent_name and not parent.name:
                parent.set_name(parent_name)
    for callback in callbacks:
        links = callback.options.get('link', [])
        callback_class = import_string(callback.task)
        _create_chain_entry(user_id, callback.id, callback_class, callback.args, callback.kwargs, links, parent=parent)


def _create_chord_entry(task_id, task_class, message_body, user_id):
    """
    Create and update status records for a new :py:class:`UserTaskMixin` in a Celery chord.
    """
    args = message_body['args']
    kwargs = message_body['kwargs']
    arguments_dict = task_class.arguments_as_dict(*args, **kwargs)
    name = task_class.generate_name(arguments_dict)
    total_steps = task_class.calculate_total_steps(arguments_dict)
    parent_name = kwargs.get('user_task_name', '')
    chord_data = message_body['chord']
    group_id = message_body['taskset']
    with transaction.atomic():
        group, created = UserTaskStatus.objects.get_or_create(
            task_id=group_id, defaults={'is_container': True, 'name': parent_name, 'task_class': 'celery.group',
                                        'total_steps': total_steps, 'user_id': user_id})
        if created:
            # Also create a status for the chord as a whole
            chord = UserTaskStatus.objects.create(
                is_container=True, name=parent_name, task_class='celery.chord', task_id=str(uuid4()),
                total_steps=total_steps, user_id=user_id)
            group.parent = chord
            group.save(update_fields={'parent', 'modified'})
        else:
            chord = None
            group.increment_total_steps(total_steps)
            if parent_name and not group.name:
                group.set_name(parent_name)
        UserTaskStatus.objects.create(
            name=name, parent=group, task_class=task_class, task_id=task_id, total_steps=total_steps, user_id=user_id)
        # chord body task status
        if not created:
            # body being handled by another of the tasks in the header
            return
        task_id = chord_data['options']['task_id']
        body_task = chord_data['task']
        body_class = import_string(body_task).__class__
        if not issubclass(body_class, UserTaskMixin):
            return
        args = chord_data['args']
        kwargs = chord_data['kwargs']
        arguments_dict = body_class.arguments_as_dict(*args, **kwargs)
        name = body_class.generate_name(arguments_dict)
        total_steps = body_class.calculate_total_steps(arguments_dict)
        UserTaskStatus.objects.get_or_create(
            task_id=task_id, defaults={'name': name, 'parent': chord, 'task_class': body_task,
                                       'total_steps': total_steps, 'user_id': user_id})
        chord.increment_total_steps(total_steps)


def _get_or_create_group_parent(message_body, user_id):
    """
    Determine if the given task belongs to a group or not, and if so, get or create a status record for the group.

    Arguments:
        message_body (dict): The body of the before_task_publish signal for the task in question
        user_id (int): The primary key of the user model record for the user who triggered the task.
                       (If using a custom user model, this may not be an integer.)

    Returns:
        UserTaskStatus: The status record for the containing group, or `None` if there isn't one
    """
    parent_id = message_body.get('taskset', None)
    if not parent_id:
        # Not part of a group
        return None
    parent_class = 'celery.group'
    parent_name = message_body['kwargs'].get('user_task_name', '')
    parent, _ = UserTaskStatus.objects.get_or_create(
        task_id=parent_id, defaults={'is_container': True, 'name': parent_name, 'task_class': parent_class,
                                     'total_steps': 0, 'user_id': user_id})
    if parent_name and not parent.name:
        parent.name = parent_name
        parent.save(update_fields={'name', 'modified'})
    return parent


def _get_user_id(arguments_dict):
    """
    Get and validate the `user_id` argument to a task derived from `UserTaskMixin`.

    Arguments:
        arguments_dict (dict): The parsed positional and keyword arguments to the task

    Returns:
        int: The primary key of a user record (may not be an int if using a custom user model)
    """
    if 'user_id' not in arguments_dict:
        raise TypeError('Each invocation of a UserTaskMixin subclass must include the user_id')
    user_id = arguments_dict['user_id']
    try:
        get_user_model().objects.get(pk=user_id)
    except (ValueError, get_user_model().DoesNotExist):
        raise TypeError('Invalid user_id: {}'.format(user_id))
    return user_id


@task_prerun.connect
def start_user_task(sender=None, **kwargs):  # pylint: disable=unused-argument
    """
    Update the status record when execution of a :py:class:`UserTaskMixin` begins.
    """
    if isinstance(sender, UserTaskMixin):
        sender.status.start()


@task_failure.connect
def task_failed(sender=None, **kwargs):
    """
    Update the status record accordingly when a :py:class:`UserTaskMixin` fails.
    """
    if isinstance(sender, UserTaskMixin):
        exception = kwargs['exception']
        if not isinstance(exception, TaskCanceledException):
            # Don't include traceback, since this is intended for end users
            sender.status.fail(str(exception))
        user_task_stopped.send_robust(sender=UserTaskStatus, status=sender.status)


@task_retry.connect
def retrying_task(sender=None, **kwargs):  # pylint: disable=unused-argument
    """
    Update the status record to reflect that a retry is pending.
    """
    if isinstance(sender, UserTaskMixin):
        sender.status.retry()


@task_success.connect
def task_succeeded(sender=None, **kwargs):  # pylint: disable=unused-argument
    """
    Update the status record accordingly when a :py:class:`UserTaskMixin` finishes successfully.
    """
    if isinstance(sender, UserTaskMixin):
        status = sender.status
        # Failed tasks with good exception handling did not succeed just because they ended cleanly
        if status.state not in (UserTaskStatus.CANCELED, UserTaskStatus.FAILED, UserTaskStatus.RETRYING):
            status.succeed()
        user_task_stopped.send_robust(sender=UserTaskStatus, status=sender.status)
