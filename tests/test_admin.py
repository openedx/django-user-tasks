#!/usr/bin/env python
"""
Tests for the ``django-user-tasks`` admin module.
"""

from django.contrib import auth
from django.test import TestCase
from django.urls import reverse

User = auth.get_user_model()


class AdminTestCase(TestCase):
    """
    Tests for the ``user_tasks`` application's Django admin pages.
    """
    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(
            username='tester',
            email='tester@example.com',
            password='password',
            is_staff=True,
            is_superuser=True,
        )
        self.client.login(username=self.user.username, password='password')

    def test_artifact_list(self):
        """
        Make sure the main UserTaskArtifact admin page loads.
        """
        response = self.client.get(reverse('admin:user_tasks_usertaskartifact_changelist'))
        assert response.status_code == 200

    def test_status_list(self):
        """
        Make sure the main UserTaskStatus admin page loads.
        """
        response = self.client.get(reverse('admin:user_tasks_usertaskstatus_changelist'))
        assert response.status_code == 200
