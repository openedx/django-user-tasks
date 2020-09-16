"""
These settings are here to use during tests, because django requires them.

In a real-world use case, apps in this project are installed into other
Django applications, so these settings will not be used.
"""

import tempfile
from os.path import abspath, dirname, join

from celery import __version__ as celery_version
from packaging import version

CELERY_VERSION = version.parse(celery_version)
results_dir = tempfile.TemporaryDirectory()


def root(*args):
    """
    Get the absolute path of the given path relative to the project root.
    """
    return join(abspath(dirname(__file__)), *args)


AUTHENTICATION_BACKENDS = (
    'rules.permissions.ObjectPermissionBackend',
    'django.contrib.auth.backends.ModelBackend',
)

BROKER_URL = 'memory://localhost/'
CELERY_IGNORE_RESULT = True

if CELERY_VERSION >= version.parse('4.0'):
    CELERY_RESULT_BACKEND = 'file://{}'.format(results_dir.name)

if CELERY_VERSION >= version.parse('4.4'):
    CELERY_RESULT_BACKEND = 'django-cache'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'default.db',
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    }
}

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.messages',
    'django.contrib.sessions',
    'django.contrib.admin',
    'rest_framework',
    'user_tasks.apps.UserTasksConfig',
]

if CELERY_VERSION >= version.parse('4.4'):
    INSTALLED_APPS.append('django-celery-results')

LOCALE_PATHS = [
    root('user_tasks', 'conf', 'locale'),
]

MEDIA_ROOT = tempfile.mkdtemp()

MIDDLEWARE = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

ROOT_URLCONF = 'test_urls'

SECRET_KEY = 'insecure-secret-key'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
    }
]

USE_TZ = True
