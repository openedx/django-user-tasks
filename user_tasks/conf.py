"""
Custom Django settings for django-user-tasks.
"""

from datetime import timedelta

from django.conf import settings as django_settings
from django.core.files.storage import default_storage as django_default_storage
from django.core.files.storage import storages
from django.utils.module_loading import import_string

from user_tasks import filters


def get_storage(import_path=None):
    """
    Return a storage backend instance.

    1. STORAGES['user_task_artifacts'] alias (Django ≥4.2 or 5.2).
    2. Explicit import path, if provided.
    3. Django’s default_storage singleton.
    """
    # New STORAGES dict lookup for user task artifacts
    storages_config = getattr(settings, 'STORAGES', {})
    if "user_task_artifacts" in storages_config:
        return storages["user_task_artifacts"]

    if import_path:
        return import_string(import_path)()

    # Final fallback
    return django_default_storage


class LazySettings():
    """
    The behavior of ``django-user-tasks`` can be customized via the following Django settings.
    """

    @property
    def USER_TASKS_ARTIFACT_FILTERS(self):  # pylint: disable=invalid-name
        """
        Tuple containing zero or more filters for UserTaskArtifact listing REST API calls.

        Each entry should be a Django REST Framework filter backend class
        object, such as ``django_filters.rest_framework.DjangoFilterBackend``.
        The default value contains only ``user_tasks.filters.ArtifactFilterBackend``,
        which allows superusers to see all artifacts but other users to see only
        those for artifacts they triggered themselves.
        """
        return getattr(django_settings, 'USER_TASKS_STATUS_FILTERS', (filters.ArtifactFilterBackend,))

    @property
    def USER_TASKS_ARTIFACT_STORAGE(self):  # pylint: disable=invalid-name
        """
        File storage backend to use for :py:attr:`user_tasks.models.UserTaskStatus.file`.

        If explicitly set, the setting should be the import path of a storage
        backend class.
        """
        import_path = getattr(django_settings, 'USER_TASKS_ARTIFACT_STORAGE', None)
        return get_storage(import_path)

    @property
    def USER_TASKS_MAX_AGE(self):  # pylint: disable=invalid-name
        """
        ``timedelta`` reflecting the age after which UserTaskStatus records should be deleted.

        For this setting to be useful, ``user_tasks.tasks.purge_old_user_tasks``
        should be configured to run on an appropriate schedule.  Note that the
        age is calculated from task creation, not completion.  The default
        value is 30 days.
        """
        return getattr(django_settings, 'USER_TASKS_MAX_AGE', timedelta(days=30))

    @property
    def USER_TASKS_STATUS_FILTERS(self):
        """
        Tuple containing zero or more filters for UserTaskStatus listing REST API calls.

        Each entry should be a Django REST Framework filter backend class
        object, such as ``django_filters.rest_framework.DjangoFilterBackend``.
        The default value contains only ``user_tasks.filters.StatusFilterBackend``,
        which allows superusers to see all task statuses but other users to see only
        those for tasks they triggered themselves.
        """
        return getattr(django_settings, 'USER_TASKS_STATUS_FILTERS', (filters.StatusFilterBackend,))


settings = LazySettings()
