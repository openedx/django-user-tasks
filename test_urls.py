"""
URLs for user_tasks test suite.
"""

from django.urls import re_path
from django.contrib import admin

from user_tasks.urls import urlpatterns

urlpatterns += [re_path(r'^admin/', admin.site.urls)]
