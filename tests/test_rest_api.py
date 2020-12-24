#!/usr/bin/env python
"""
Tests for the ``django-user-tasks`` REST API.
"""

import logging
from datetime import timedelta
from uuid import uuid4

import mock
import rules

from django.contrib import auth
from django.urls import reverse
from django.utils.timezone import now

from rest_framework.test import APITestCase

from user_tasks.models import UserTaskArtifact, UserTaskStatus
from user_tasks.rules import add_rules
from user_tasks.serializers import ArtifactSerializer, StatusSerializer

User = auth.get_user_model()

LOGGER = logging.getLogger(__name__)


# Helper functions for stuff that pylint complains about without disable comments

def _context(response):
    """
    Get a context dictionary for a serializer appropriate for the given response.
    """
    return {'request': response.wsgi_request}  # pylint: disable=no-member


def _data(response):
    """
    Get the serialized data dictionary from the given REST API test response.
    """
    return response.data  # pylint: disable=no-member


class TestRestApi(APITestCase):
    """
    Tests of the REST API calls.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        add_rules()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        rules.rulesets.default_rules.clear()

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = User.objects.create_user('test_user', 'test@example.com', 'password')
        cls.superuser = User.objects.create_superuser('admin', 'admin@example.com', 'password')
        cls.other_user = User.objects.create_user('other_user', 'other@example.com', 'password')
        cls.status = UserTaskStatus.objects.create(
            user=cls.user, task_id=str(uuid4()), task_class='test_rest_api.sample_task', name='SampleTask 2',
            total_steps=5)
        cls.artifact = UserTaskArtifact.objects.create(status=cls.status, text='Lorem ipsum')
        cls.older_status = UserTaskStatus.objects.create(
            user=cls.user, task_id=str(uuid4()), task_class='test_rest_api.sample_task', name='SampleTask 1',
            total_steps=5)
        yesterday = now() - timedelta(days=1)
        UserTaskStatus.objects.filter(pk=cls.older_status.id).update(created=yesterday, modified=yesterday)

    def setUp(self):
        super().setUp()
        self.status.refresh_from_db()
        self.older_status.refresh_from_db()

    def test_artifact_detail(self):
        """Users should be able to access artifacts for tasks they triggered."""
        self._login(self.user)
        response = self.client.get(reverse('usertaskartifact-detail', args=[self.artifact.uuid]))
        assert response.status_code == 200
        serializer = ArtifactSerializer(self.artifact, context=_context(response))
        assert _data(response) == serializer.data

    def test_artifact_detail_anonymous(self):
        """Anonymous users should be unable to access task artifacts via the API."""
        response = self.client.get(reverse('usertaskartifact-detail', args=[self.artifact.uuid]))
        assert response.status_code == 403

    def test_artifact_detail_superuser(self):
        """Superusers should be able to access artifacts for all tasks."""
        self._login(self.superuser)
        response = self.client.get(reverse('usertaskartifact-detail', args=[self.artifact.uuid]))
        assert response.status_code == 200
        serializer = ArtifactSerializer(self.artifact, context=_context(response))
        assert _data(response) == serializer.data

    def test_artifact_detail_other_user(self):
        """Users should be unable to access artifacts for another user's tasks via the API."""
        self._login(self.other_user)
        response = self.client.get(reverse('usertaskartifact-detail', args=[self.artifact.uuid]))
        assert response.status_code == 404

    def test_artifact_list(self):
        """Users should be able to access a list of their tasks' artifacts."""
        self._login(self.user)
        response = self.client.get(reverse('usertaskartifact-list'))
        assert response.status_code == 200
        serializer = ArtifactSerializer(self.artifact, context=_context(response))
        assert _data(response) == [serializer.data]

    def test_artifact_list_anonymous(self):
        """Anonymous should be unable to access lists of task artifacts."""
        response = self.client.get(reverse('usertaskartifact-list'))
        assert response.status_code == 403

    def test_artifact_list_superuser(self):
        """Superusers should be able to access a list of all artifacts."""
        self._login(self.superuser)
        response = self.client.get(reverse('usertaskartifact-list'))
        assert response.status_code == 200
        serializer = ArtifactSerializer(self.artifact, context=_context(response))
        assert _data(response) == [serializer.data]

    def test_artifact_list_other_user(self):
        """Users should be unable to see artifacts for other users in their task artifact list."""
        self._login(self.other_user)
        response = self.client.get(reverse('usertaskartifact-list'))
        assert response.status_code == 200
        assert _data(response) == []

    def test_status_cancel(self):
        """Users should be able to cancel tasks they no longer wish to complete."""
        self._login(self.user)
        response = self.client.post(reverse('usertaskstatus-cancel', args=[self.status.uuid]))
        assert response.status_code == 200
        self.status.refresh_from_db()
        assert self.status.state == UserTaskStatus.CANCELED

    def test_status_cancel_anonymous(self):
        """Anonymous users should be unable to cancel tasks."""
        response = self.client.post(reverse('usertaskstatus-cancel', args=[self.status.uuid]))
        assert response.status_code == 403
        self.status.refresh_from_db()
        assert self.status.state == UserTaskStatus.PENDING

    def test_status_cancel_superuser(self):
        """Superusers should be able to cancel any task."""
        self._login(self.superuser)
        response = self.client.post(reverse('usertaskstatus-cancel', args=[self.status.uuid]))
        assert response.status_code == 200
        self.status.refresh_from_db()
        assert self.status.state == UserTaskStatus.CANCELED

    def test_status_cancel_other_user(self):
        """Users should be unable to cancel the tasks of other users."""
        self._login(self.other_user)
        response = self.client.post(reverse('usertaskstatus-cancel', args=[self.status.uuid]))
        assert response.status_code == 404
        self.status.refresh_from_db()
        assert self.status.state == UserTaskStatus.PENDING

    @mock.patch('django.contrib.auth.models.User.has_perm')
    def test_status_cancel_view_only(self, mock_has_perm):
        """A user with view but not cancel permission on a status record should be unable to cancel it."""
        def no_cancel(permission, status):  # pylint: disable=unused-argument
            """Deny user_tasks.cancel_usertaskstatus permission for any particular status record."""
            if permission == 'user_tasks.cancel_usertaskstatus':
                return status is None
            return True
        mock_has_perm.side_effect = no_cancel
        self._login(self.user)
        response = self.client.post(reverse('usertaskstatus-cancel', args=[self.status.uuid]))
        assert response.status_code == 403
        self.status.refresh_from_db()
        assert self.status.state == UserTaskStatus.PENDING

    def test_status_delete(self):
        """Users should be able to delete their own task status records when they're done with them."""
        self._login(self.user)
        response = self.client.delete(reverse('usertaskstatus-detail', args=[self.status.uuid]))
        assert response.status_code == 204
        assert not UserTaskStatus.objects.filter(pk=self.status.id).exists()

    def test_status_delete_anonymous(self):
        """Anonymous users should not be able to delete task status records."""
        response = self.client.delete(reverse('usertaskstatus-detail', args=[self.status.uuid]))
        assert response.status_code == 403
        assert UserTaskStatus.objects.filter(pk=self.status.id).exists()

    def test_status_delete_superuser(self):
        """Users should be able to delete their own task status records when they're done with them."""
        self._login(self.superuser)
        response = self.client.delete(reverse('usertaskstatus-detail', args=[self.status.uuid]))
        assert response.status_code == 204
        assert not UserTaskStatus.objects.filter(pk=self.status.id).exists()

    def test_status_delete_other_user(self):
        """Users should not be able to delete the task status records of other users."""
        self._login(self.other_user)
        response = self.client.delete(reverse('usertaskstatus-detail', args=[self.status.uuid]))
        assert response.status_code == 404
        assert UserTaskStatus.objects.filter(pk=self.status.id).exists()

    def test_status_detail(self):
        """Users should be able to access status records for tasks they triggered."""
        self._login(self.user)
        response = self.client.get(reverse('usertaskstatus-detail', args=[self.status.uuid]))
        assert response.status_code == 200
        serializer = StatusSerializer(self.status, context=_context(response))
        assert _data(response) == serializer.data

    def test_status_detail_anonymous(self):
        """Anonymous users should be unable to access task status records via the API."""
        response = self.client.get(reverse('usertaskstatus-detail', args=[self.status.uuid]))
        assert response.status_code == 403

    def test_status_detail_superuser(self):
        """Superusers should be able to access all status records."""
        self._login(self.superuser)
        response = self.client.get(reverse('usertaskstatus-detail', args=[self.status.uuid]))
        assert response.status_code == 200
        serializer = StatusSerializer(self.status, context=_context(response))
        assert _data(response) == serializer.data

    def test_status_detail_other_user(self):
        """Users should be unable to access status records for another user's tasks via the API."""
        self._login(self.other_user)
        response = self.client.get(reverse('usertaskstatus-detail', args=[self.status.uuid]))
        assert response.status_code == 404

    def test_status_list(self):
        """Users should be able to access a list of their tasks' status records."""
        self._login(self.user)
        response = self.client.get(reverse('usertaskstatus-list'))
        assert response.status_code == 200
        serializer = StatusSerializer(
            [self.status, self.older_status], context=_context(response), many=True)
        assert _data(response) == serializer.data

    def test_status_list_anonymous(self):
        """Anonymous should be unable to access lists of task status records."""
        response = self.client.get(reverse('usertaskstatus-list'))
        assert response.status_code == 403

    def test_status_list_superuser(self):
        """Superusers should be able to access a list of all task status records."""
        self._login(self.superuser)
        response = self.client.get(reverse('usertaskstatus-list'))
        assert response.status_code == 200
        serializer = StatusSerializer(
            [self.status, self.older_status], context=_context(response), many=True)
        assert _data(response) == serializer.data

    def test_status_list_other_user(self):
        """Users should be unable to see tasks for other users in their task status list."""
        self._login(self.other_user)
        response = self.client.get(reverse('usertaskstatus-list'))
        assert response.status_code == 200
        assert _data(response) == []

    def _login(self, user):
        """
        Log the test client in as the specified user.
        """
        self.client.force_authenticate(user)  # pylint: disable=no-member
