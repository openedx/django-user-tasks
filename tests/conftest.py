"""
Configuration code for pytest runs.
"""

import pytest
from celery import Celery

from django.conf import settings


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
    # The try/except blocks are to work around a Python 3.5 bug: https://bugs.python.org/issue22427
    # They can be removed once we stop testing under Python 3.5 in edx-platform (coming soon)
    try:
        settings.MEDIA_DIR.cleanup()
    except FileNotFoundError:
        pass
    try:
        settings.RESULTS_DIR.cleanup()
    except FileNotFoundError:
        pass
