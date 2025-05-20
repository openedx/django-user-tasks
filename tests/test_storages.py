""" Storages tests."""
from storages.backends.s3boto3 import S3Boto3Storage

from django.core.files.storage import FileSystemStorage
from django.test import TestCase, override_settings

from user_tasks.conf import get_storage
from user_tasks.conf import settings as user_tasks_settings


class TestUserTaskStatus(TestCase):
    """ Test cases for storages."""

    @override_settings(
        USER_TASKS_ARTIFACT_STORAGE="storages.backends.s3boto3.S3Boto3Storage"
    )
    def test_storage_from_import_path(self):
        """
        Test that providing an explicit import path to get_storage()
        returns the correct storage backend.
        """
        storage = get_storage("storages.backends.s3boto3.S3Boto3Storage")
        assert isinstance(storage, S3Boto3Storage)

    def test_storage_fallback_to_default(self):
        """
        Test that get_storage() returns Django's default storage
        when no import path is provided and no STORAGES dict is defined.
        """
        storage = get_storage()
        assert isinstance(storage, FileSystemStorage)

    def test_storage_from_storages_dict(self):
        """
        Test that get_storage() returns the storage instance defined
        under STORAGES["user_task_artifacts"] when present.

        Since LazySettings does not expose STORAGES from Django settings directly,
        we monkey-patch it on the user_tasks_settings object.
        """
        # pylint: disable=literal-used-as-attribute
        setattr(user_tasks_settings, 'STORAGES', {
            "default": {
                "BACKEND": "django.core.files.storage.FileSystemStorage",
            },
            "user_task_artifacts": {
                "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
                "OPTIONS": {
                    "bucket_name": "tasks",
                    "location": "tasks/images",
                }
            }
        })

        storage = get_storage()
        assert isinstance(storage, S3Boto3Storage)
        assert storage.location == "tasks/images"
