"""
Configuration code for pytest runs.
"""

import pytest
from celery import Celery


@pytest.fixture(autouse=True, scope='session')
def start_celery_app():
    """
    Initialize the celery app after Django settings have finished initializing.
    """
    app = Celery('user_tasks')
    app.conf.task_protocol = 1
    app.config_from_object('django.conf:settings')


@pytest.fixture(autouse=True, scope='session')
def manage_temp_dirs():
    """
    Explicitly clean up the temporary directories created in test_settings.py when the test session ends.
    """
    yield
    from django.conf import settings
    settings.MEDIA_DIR.cleanup()
    settings.RESULTS_DIR.cleanup()
