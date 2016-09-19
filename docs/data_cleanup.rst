Data Cleanup
============

After running django-user-tasks for a while, you'll typically have an
assortment of :py:class:`UserTaskStatus` and :py:class:`UserTaskArtifact`
records sitting around in the database.  These can be either explicitly
removed or automatically cleaned up.

Explicit
--------

A :py:class:`UserTaskStatus` and any associated :py:class:`UserTaskArtifact`
instances can be deleted via the REST API by a user with appropriate
permissions.  It's usually appropriate to put a button for this in the UI
wherever a status is shown as long as the task has reached a final state:
``Canceled``, ``Failed``, or ``Succeeded``.  Note that if you delete a
status record before the task has finished processing, it may be recreated
upon the next state transition.

.. _automatic-cleanup:

Automatic
---------

:py:func:`user_tasks.tasks.purge_old_user_tasks` is a Celery task which
deletes any :py:class:`UserTaskArtifact` records (and any associated
artifacts) which were created more than a certain duration ago.  The
task can be run explicitly, but you'd typically want it to run periodically
by adding it to Celery's ``CELERYBEAT_SCHEDULE`` setting.

The maximum age for status records defaults to 30 days, but can be
customized by assigning a suitable ``timedelta`` to the
``USER_TASKS_MAX_AGE`` setting.
