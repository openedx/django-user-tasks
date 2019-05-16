#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Tests for the REST API model serializers.
"""

from __future__ import absolute_import, unicode_literals

import shutil
from uuid import uuid4

from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.utils.timezone import localtime

from rest_framework.test import APIRequestFactory

from user_tasks.models import UserTaskArtifact, UserTaskStatus
from user_tasks.serializers import ArtifactSerializer, StatusSerializer


def _format(datetime):
    """
    Generate the same text representation of the given datetime that DRF would.
    """
    return localtime(datetime).isoformat()


class TestStatusSerializer(TestCase):
    """
    Tests of the serializer for UserTaskStatus model instances.
    """

    @classmethod
    def setUpTestData(cls):
        super(TestStatusSerializer, cls).setUpTestData()
        cls.user = User.objects.create_user('test_user', 'test@example.com', 'password')

    def test_output(self):
        """The serializer should generate the expected data for a status record."""
        status = UserTaskStatus.objects.create(user=self.user, task_id=str(uuid4()), name='SampleTask', total_steps=4)
        expected = {
            'name': 'SampleTask',
            'state': 'Pending',
            'state_text': 'Pending',
            'completed_steps': 0,
            'total_steps': 4,
            'attempts': 1,
            'created': _format(status.created),
            'modified': _format(status.modified),
            'artifacts': []
        }
        serializer = StatusSerializer(status)
        assert serializer.data == expected

    def test_output_with_artifact(self):
        """The serializer should include URLs for any generated artifacts."""
        status = UserTaskStatus.objects.create(user=self.user, task_id=str(uuid4()), name='SampleTask', total_steps=4)
        artifact = UserTaskArtifact.objects.create(status=status, text='Lorem Ipsum')
        expected = {
            'name': 'SampleTask',
            'state': 'Pending',
            'state_text': 'Pending',
            'completed_steps': 0,
            'total_steps': 4,
            'attempts': 1,
            'created': _format(status.created),
            'modified': _format(status.modified),
            'artifacts': ['http://testserver/artifacts/{}/'.format(artifact.uuid)]
        }
        request = APIRequestFactory().get(reverse('usertaskstatus-detail', args=[status.uuid]))
        serializer = StatusSerializer(status, context={'request': request})
        assert serializer.data == expected


class TestArtifactSerializer(TestCase):
    """
    Tests of the serializer for UserTaskArtifact model instances
    """

    @classmethod
    def setUpTestData(cls):
        super(TestArtifactSerializer, cls).setUpTestData()
        user = User.objects.create_user('test_user', 'test@example.com', 'password')
        cls.status = UserTaskStatus.objects.create(user=user, task_id=str(uuid4()), name='SampleTask', total_steps=4)

    @classmethod
    def tearDownClass(cls):
        super(TestArtifactSerializer, cls).tearDownClass()
        # Clean up temp files
        shutil.rmtree(settings.MEDIA_ROOT)

    def test_file(self):
        """The serializer should handle file artifacts correctly."""
        uploaded_file = SimpleUploadedFile('filename.txt', b'Content of the file')
        artifact = UserTaskArtifact.objects.create(status=self.status, file=uploaded_file)
        expected = {
            'status': 'http://testserver/tasks/{}/'.format(self.status.uuid),
            'name': 'Output',
            'created': _format(artifact.created),
            'modified': _format(artifact.modified),
            'file': artifact.file.url,
            'text': '',
            'url': '',
        }
        request = APIRequestFactory().get(reverse('usertaskartifact-detail', args=[artifact.uuid]))
        serializer = ArtifactSerializer(artifact, context={'request': request})
        assert serializer.data == expected

    def test_text(self):
        """The serializer should handle text block artifacts correctly."""
        artifact = UserTaskArtifact.objects.create(status=self.status, text='Got your output right here.')
        expected = {
            'status': 'http://testserver/tasks/{}/'.format(self.status.uuid),
            'name': 'Output',
            'created': _format(artifact.created),
            'modified': _format(artifact.modified),
            'file': '',
            'text': artifact.text,
            'url': '',
        }
        request = APIRequestFactory().get(reverse('usertaskartifact-detail', args=[artifact.uuid]))
        serializer = ArtifactSerializer(artifact, context={'request': request})
        assert serializer.data == expected

    def test_url(self):
        """The serializer should handle URL artifacts correctly."""
        artifact = UserTaskArtifact.objects.create(status=self.status, url='http://www.example.com/output/3/')
        expected = {
            'status': 'http://testserver/tasks/{}/'.format(self.status.uuid),
            'name': 'Output',
            'created': _format(artifact.created),
            'modified': _format(artifact.modified),
            'file': '',
            'text': '',
            'url': artifact.url,
        }
        request = APIRequestFactory().get(reverse('usertaskartifact-detail', args=[artifact.uuid]))
        serializer = ArtifactSerializer(artifact, context={'request': request})
        assert serializer.data == expected
