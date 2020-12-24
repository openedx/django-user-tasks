#!/usr/bin/env python
"""
Tests for the user_tasks subclasses of celery.Task.
"""

import logging
from datetime import timedelta
from uuid import uuid4

from celery import Task, shared_task

from django.contrib import auth
from django.test import TestCase, override_settings
from django.utils.timezone import now

from user_tasks.models import UserTaskArtifact, UserTaskStatus
from user_tasks.tasks import UserTask, UserTaskMixin, purge_old_user_tasks

User = auth.get_user_model()

LOGGER = logging.getLogger(__name__)


class MinimalTask(Task, UserTaskMixin):  # pylint: disable=abstract-method
    """
    A minimal UserTaskMixin subclass which uses the default name and total_steps generation.
    """


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


class TestUserTasks(TestCase):
    """
    Tests of UserTaskMixin and UserTask.
    """

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
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


@override_settings(CELERY_ALWAYS_EAGER=True)
class TestPurgeOldUserTasks(TestCase):
    """
    Tests of the Celery cleanup task for old user task database records.
    """

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = User.objects.create_user('test_user', 'test@example.com', 'password')

    def test_old_data(self):
        """The cleanup task should purge old database records."""
        self._create_records(now() - timedelta(days=31))
        purge_old_user_tasks.delay()
        assert UserTaskStatus.objects.count() == 0
        assert UserTaskArtifact.objects.count() == 0

    def test_recent_data(self):
        """The cleanup task should leave recent database records intact."""
        self._create_records(now() - timedelta(days=29))
        purge_old_user_tasks.delay()
        assert UserTaskStatus.objects.count() == 1
        assert UserTaskArtifact.objects.count() == 1

    def test_mixed_data(self):
        """The cleanup task should purge only old database records."""
        self._create_records(now() - timedelta(days=29))
        status = UserTaskStatus.objects.all()[0]
        self._create_records(now() - timedelta(days=31))
        purge_old_user_tasks.delay()
        assert UserTaskStatus.objects.count() == 1
        assert UserTaskArtifact.objects.count() == 1
        assert UserTaskStatus.objects.filter(pk=status.id).exists()

    def _create_records(self, created):
        """
        Create a UserTaskStatus and UserTaskArtifact with the specified creation date.
        """
        data = {
            'name': 'SampleTask', 'state': UserTaskStatus.SUCCEEDED, 'task_class': 'test_tasks.sample_task',
            'task_id': str(uuid4()), 'total_steps': 5, 'user': self.user
        }
        status = UserTaskStatus.objects.create(**data)
        completed = created + timedelta(hours=1)
        UserTaskStatus.objects.filter(pk=status.id).update(created=created, modified=completed)
        artifact = UserTaskArtifact.objects.create(status=status, text='Lorem ipsum')
        UserTaskArtifact.objects.filter(pk=artifact.id).update(created=completed, modified=completed)
