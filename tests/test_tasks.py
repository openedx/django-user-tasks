#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Tests for the user_tasks subclasses of celery.Task.
"""

from __future__ import absolute_import, print_function, unicode_literals

import logging

from django.contrib.auth.models import User
from django.test import TestCase

from celery import shared_task, Task

from user_tasks.models import UserTaskStatus
from user_tasks.tasks import UserTask, UserTaskMixin

LOGGER = logging.getLogger(__name__)


class MinimalTask(Task, UserTaskMixin):  # pylint: disable=abstract-method
    """
    A minimal UserTaskMixin subclass which uses the default name and total_steps generation.
    """
    pass


@shared_task(base=MinimalTask, bind=True)
def minimal_task(self, user_id, argument, **kwargs):  # pylint: disable=unused-argument
    """
    Example usage of the MinimalTask class.
    """
    return argument


class SampleTask(UserTask):  # pylint: disable=abstract-method
    """
    Small UserTask subclass for use in test cases.
    """

    @classmethod
    def generate_name(cls, arguments_dict):
        arg1 = arguments_dict['arg1']
        arg2 = arguments_dict['arg2']
        return 'SampleTask: {}, {}'.format(arg1, arg2)

    @staticmethod
    def calculate_total_steps(arguments_dict):
        arg1 = arguments_dict['arg1']
        arg2 = arguments_dict['arg2']
        return arg1 * arg2


@shared_task(base=SampleTask, bind=True)
def sample_task(self, user_id, arg1, arg2, **kwargs):  # pylint: disable=unused-argument
    """
    Example of a specific task inheriting from UserTask.
    """
    return arg1, arg2


class TestTasks(TestCase):
    """
    Tests of UserTaskMixin and UserTask.
    """

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user('test_user', 'test@example.com', 'password')

    def test_generate_name_omitted(self):
        """Using UserTaskMixin without generate_name() implemented should default to the task function name."""
        minimal_task.delay(self.user.id, 'Argument')
        statuses = UserTaskStatus.objects.all()
        assert len(statuses) == 1
        assert statuses[0].name == 'minimal_task'

    def test_generate_name(self):
        """generate_name() should be able to generate a task name based on the task's arguments."""
        result = sample_task.delay(self.user.id, 1, 2)
        status = UserTaskStatus.objects.get(task_id=result.id)
        assert status.name == 'SampleTask: 1, 2'

        result = sample_task.delay(self.user.id, 3, arg2=4)
        status = UserTaskStatus.objects.get(task_id=result.id)
        assert status.name == 'SampleTask: 3, 4'

        result = sample_task.delay(arg2=6, arg1=5, user_id=self.user.id)
        status = UserTaskStatus.objects.get(task_id=result.id)
        assert status.name == 'SampleTask: 5, 6'

    def test_calculate_total_steps(self):
        """calculate_total_steps() should generate the total_steps value based on the task's arguments."""
        result = sample_task.delay(self.user.id, 1, 2)
        status = UserTaskStatus.objects.get(task_id=result.id)
        assert status.total_steps == 2

        result = sample_task.delay(self.user.id, 3, arg2=4)
        status = UserTaskStatus.objects.get(task_id=result.id)
        assert status.total_steps == 12

        result = sample_task.delay(arg2=6, arg1=5, user_id=self.user.id)
        status = UserTaskStatus.objects.get(task_id=result.id)
        assert status.total_steps == 30
