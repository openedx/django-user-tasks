#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sample implementation of authorization rules for the ``django-user-tasks`` permissions.

Requires use of the ``rules`` package.  The rule implementations aren't
registered by default because that would interfere with the ability to use
custom rules.)  You can register them in another application's ``rules.py``:

.. code-block:: python

    import user_tasks

    user_tasks.rules.add_rules()
"""

from __future__ import absolute_import, unicode_literals

import rules


@rules.predicate
def is_status_creator(user, status=None):
    """
    Check for ownership of the provided status.

    Arguments:
        user (User): The user for whom a permission check is being made.
        status (UserTaskStatus): The status record to check ownership for.

    Returns:
        bool: True if no status is provided or the user owns the given status.
    """
    if not status:
        return True
    return status.user_id == user.id


@rules.predicate
def is_artifact_creator(user, artifact=None):
    """
    Check for ownership of the provided artifact.

    Arguments:
        user (User): The user for whom a permission check is being made.
        artifact (UserTaskArtifact): The artifact to check ownership for.

    Returns:
        bool: True if no artifact is provided or the user owns the given artifact.
    """
    if not artifact:
        return True
    return is_status_creator(user, artifact.status)

STATUS_PERMISSION = is_status_creator | rules.predicates.is_superuser
ARTIFACT_PERMISSION = is_artifact_creator | rules.predicates.is_superuser


def add_rules():
    """
    Use the rules provided in this module to implement authorization checks for the ``django-user-tasks`` models.

    These rules allow only superusers and the user who triggered a task to view its status or artifacts, cancel the
    task, or delete the status information and all its related artifacts.  Only superusers are allowed to directly
    modify or delete an artifact (or to modify a task status record).
    """
    rules.add_perm('user_tasks.view_usertaskstatus', STATUS_PERMISSION)
    rules.add_perm('user_tasks.cancel_usertaskstatus', STATUS_PERMISSION)
    rules.add_perm('user_tasks.change_usertaskstatus', rules.predicates.is_superuser)
    rules.add_perm('user_tasks.delete_usertaskstatus', STATUS_PERMISSION)
    rules.add_perm('user_tasks.view_usertaskartifact', ARTIFACT_PERMISSION)
    rules.add_perm('user_tasks.change_usertaskartifact', rules.predicates.is_superuser)
    rules.add_perm('user_tasks.delete_usertaskartifact', rules.predicates.is_superuser)
