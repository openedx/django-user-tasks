# -*- coding: utf-8 -*-
"""
Custom exception classes.
"""

from __future__ import absolute_import, unicode_literals


class TaskCanceledException(RuntimeError):
    """
    Raised to stop task execution when a cancellation command is noticed.
    """

    pass
