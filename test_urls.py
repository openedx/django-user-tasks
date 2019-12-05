# -*- coding: utf-8 -*-
"""
URLs for user_tasks test suite.
"""
from __future__ import absolute_import, unicode_literals

from django.conf.urls import url
from django.contrib import admin

from user_tasks.urls import urlpatterns

urlpatterns += [url(r'^admin/', admin.site.urls)]
