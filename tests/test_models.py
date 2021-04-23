#!/usr/bin/env python
"""
Tests for the `django-user-tasks` models module.
"""

import logging
from uuid import uuid4

import pytest

from django.contrib import auth
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from user_tasks.exceptions import TaskCanceledException
from user_tasks.models import UserTaskArtifact, UserTaskStatus

User = auth.get_user_model()

LOGGER = logging.getLogger(__name__)


class TestUserTaskStatus(TestCase):
    """
    Tests of the UserTask model.
    """

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = User.objects.create_user('test_user', 'test@example.com', 'password')

    def test_cancel_parent(self):
        """Canceling a container status should also cancel its children."""
        parent = self._status(is_container=True, state=UserTaskStatus.PENDING)
        status = self._status(parent=parent, state=UserTaskStatus.PENDING)
        parent.cancel()
        status.refresh_from_db()
        assert parent.state == UserTaskStatus.CANCELED
        assert status.state == UserTaskStatus.CANCELED

    def test_cancel_finished_task(self):
        """Attempting to cancel an already-finished task should have no effect."""
        status = self._status(state=UserTaskStatus.SUCCEEDED)
        status.cancel()
        assert status.state == UserTaskStatus.SUCCEEDED

    def test_fail_with_parent(self):
        """A task which fails should also mark any parent as having failed."""
        parent = self._status(is_container=True)
        status = self._status(parent=parent)
        status.fail('Oops!')
        parent.refresh_from_db()
        assert status.state == UserTaskStatus.FAILED
        assert parent.state == UserTaskStatus.FAILED
        artifact = UserTaskArtifact.objects.get(status=status)
        assert artifact.text == 'Oops!'
        parent_artifact = UserTaskArtifact.objects.get(status=parent)
        assert parent_artifact.text == 'Oops!'

    def test_increment_completed_steps(self):
        """increment_completed_steps() should update both the current status and any parent status."""
        parent = self._status(is_container=True, total_steps=0)
        status = self._status(parent=parent, total_steps=2)
        status.increment_completed_steps()
        parent.refresh_from_db()
        assert status.completed_steps == 1
        assert parent.completed_steps == 1

    def test_increment_completed_steps_explicit_steps(self):
        """increment_completed_steps() should support explicit step counts greater than 1."""
        status = self._status(total_steps=5)
        status.increment_completed_steps(3)
        assert status.completed_steps == 3
        status.refresh_from_db()
        assert status.completed_steps == 3

    def test_increment_total_steps(self):
        """increment_total_steps() should correctly update the status and any parent."""
        parent = self._status(is_container=True, total_steps=3)
        self._status(parent=parent, total_steps=2)
        status = self._status(parent=parent, total_steps=1)
        status.increment_total_steps(2)
        parent.refresh_from_db()
        assert status.total_steps == 3
        assert parent.total_steps == 5

    def test_retry(self):
        """retry() should update the status fields accordingly and not impact any parent."""
        parent = self._status(is_container=True)
        status = self._status(parent=parent)
        status.retry()
        parent.refresh_from_db()
        assert status.state == UserTaskStatus.RETRYING
        assert status.attempts == 2
        assert parent.state == UserTaskStatus.IN_PROGRESS

    def test_set_name(self):
        """set_name() should update both the subject and any parent."""
        parent = self._status(is_container=True)
        status = self._status(parent=parent)
        status.set_name('New Name')
        parent.refresh_from_db()
        assert status.name == 'New Name'
        assert parent.name == 'New Name'

    def test_set_state(self):
        """It should be possible to set a custom state for a UserTaskStatus."""
        status = self._status()
        status.set_state('Custom State')
        assert status.state == 'Custom State'
        status.refresh_from_db()
        assert status.state == 'Custom State'

    def test_set_state_canceled(self):
        """Setting a custom state for a canceled task should fail."""
        status = self._status(state=UserTaskStatus.CANCELED)
        with pytest.raises(TaskCanceledException):
            status.set_state('Custom State')
        assert status.state == UserTaskStatus.CANCELED
        status.refresh_from_db()
        assert status.state == UserTaskStatus.CANCELED

    def test_set_state_parent(self):
        """Setting a custom state should propagate to the state's parent."""
        parent = self._status(is_container=True, task_class='celery.chain')
        status = self._status(parent=parent)
        status.set_state('Custom State')
        assert status.state == 'Custom State'
        status.refresh_from_db()
        assert status.state == 'Custom State'
        assert parent.state == 'Custom State'
        parent.refresh_from_db()
        assert parent.state == 'Custom State'

    def test_start(self):
        """The start() method should update the status record appropriately."""
        status = self._status(state=UserTaskStatus.PENDING)
        assert status.state == UserTaskStatus.PENDING
        status.start()
        assert status.state == UserTaskStatus.IN_PROGRESS
        status.refresh_from_db()
        assert status.state == UserTaskStatus.IN_PROGRESS

    def test_start_canceled_task(self):
        """Attempting to start a canceled task should raise a TaskCanceledException."""
        status = self._status(state=UserTaskStatus.CANCELED)
        with pytest.raises(TaskCanceledException):
            status.start()
        assert status.state == UserTaskStatus.CANCELED

    def test_start_with_failed_sibling(self):
        """If a sibling task has already failed, the parent status should not change when the task starts."""
        parent = self._status(is_container=True, state=UserTaskStatus.FAILED)
        self._status(parent=parent, state=UserTaskStatus.FAILED)
        child2 = self._status(parent=parent, state=UserTaskStatus.PENDING)
        child2.start()
        parent.refresh_from_db()
        assert child2.state == UserTaskStatus.IN_PROGRESS
        assert parent.state == UserTaskStatus.FAILED

    def test_start_with_parent(self):
        """Starting a pending task should also update any parent task status."""
        parent = self._status(is_container=True, state=UserTaskStatus.PENDING)
        status = self._status(parent=parent, state=UserTaskStatus.PENDING)
        status.start()
        assert status.state == UserTaskStatus.IN_PROGRESS
        parent.refresh_from_db()
        assert parent.state == UserTaskStatus.IN_PROGRESS

    def test_string_representation(self):
        """UserTaskStatus instances should have a reasonable string representation."""
        status = self._status()
        assert str(status) == '<UserTaskStatus: SampleTask>'

    def test_succeed(self):
        """succeed() should update its parent only if all its other children have already succeeded."""
        parent = self._status(is_container=True, total_steps=10)
        child1 = self._status(parent=parent)
        child2 = self._status(parent=parent)
        child1.succeed()
        parent.refresh_from_db()
        assert child1.state == UserTaskStatus.SUCCEEDED
        assert child1.completed_steps == child1.total_steps
        assert parent.state == UserTaskStatus.IN_PROGRESS
        assert parent.completed_steps == child1.total_steps
        child2.succeed()
        parent.refresh_from_db()
        assert child2.state == UserTaskStatus.SUCCEEDED
        assert child2.completed_steps == child2.total_steps
        assert parent.state == UserTaskStatus.SUCCEEDED
        assert parent.completed_steps == child1.total_steps + child2.total_steps

    def _status(self, **kwargs):
        """Generate a sample UserTaskStatus instance, optionally overriding fields with keyword arguments."""
        data = {
            'name': 'SampleTask', 'state': UserTaskStatus.IN_PROGRESS, 'task_class': 'test_models.sample_task',
            'task_id': str(uuid4()), 'total_steps': 5, 'user': self.user}
        data.update(kwargs)
        return UserTaskStatus.objects.create(**data)


class TestUserTaskArtifact(TestCase):
    """
    Tests of the UserTaskArtifact model.
    """

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = User.objects.create_user('test_user', 'test@example.com', 'password')

    def test_file_string(self):
        """File-based UserTaskArtifacts should have a reasonable string representation"""
        status = self._status()
        uploaded_file = SimpleUploadedFile('file.txt', b'File content')
        artifact = UserTaskArtifact(status=status, file=uploaded_file)
        assert str(artifact) == '<UserTaskArtifact: (Output) file.txt>'

    def test_text_string(self):
        """Text-based UserTaskArtifacts should have a reasonable string representation."""
        status = self._status()
        artifact = UserTaskArtifact(status=status, text='This was the output text.')
        assert str(artifact) == '<UserTaskArtifact: (Output) This was the output text.>'

    def test_long_text_string(self):
        """Long text artifacts should be cropped for the string representation."""
        status = self._status()
        text = 'blah ' * 50
        artifact = UserTaskArtifact(status=status, name='Cropped', text=text)
        assert str(artifact) == '<UserTaskArtifact: (Cropped) {}>'.format(text[:47] + '...')

    def test_url_string(self):
        """URL-based UserTaskArtifacts should have a reasonable string representation."""
        status = self._status()
        artifact = UserTaskArtifact(status=status, url='http://www.edx.org/')
        assert str(artifact) == '<UserTaskArtifact: (Output) http://www.edx.org/>'

    def _status(self, **kwargs):
        """Generate a sample UserTaskStatus instance, optionally overriding fields with keyword arguments."""
        data = {
            'name': 'SampleTask', 'state': UserTaskStatus.IN_PROGRESS, 'task_class': 'test_models.sample_task',
            'task_id': str(uuid4()), 'total_steps': 5, 'user': self.user}
        data.update(kwargs)
        return UserTaskStatus.objects.create(**data)
