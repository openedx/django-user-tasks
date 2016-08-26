Linked Tasks
============

Sometimes a task lends itself to being performed in multiple parallel
processes, or takes long enough that it should logically be broken down into
several sequential tasks.  Celery 3.0 added explicit support for linking tasks
together in a few different ways, and ``django-user-tasks`` generally supports
these.  The ones which have been specifically tested so far are listed below.

Note that it's usually best for all of the tasks in a grouping to inherit from
:py:class:`UserTaskMixin` if any of them do.  Any tasks in the group which do
not inherit from that class won't be factored into the status of the grouping
as a whole.

Chains
------

A :py:class:`~celery.chain` is a sequence of Celery tasks, where the
completion of one task in the chain causes the next one to be sent to the
broker for a worker process to start working on.  ``django-user-tasks``
recognizes such chains and creates a separate status record for the chain as
a whole if any of the tasks within it inherit from :py:class:`UserTaskMixin`.
Each task in the chain which has that mixin will update its own status
record and propagate changes to the overall chain status record as
appropriate.

The individual tasks in the chain will each have their
:py:attr:`~UserTaskStatus.parent` field set to the status record for the whole
chain, while the parent status will have the following characteristics:

* :py:attr:`~UserTaskStatus.name` is set by providing a "user_task_name"
  keyword argument to at least one of the child tasks (if none of them do so,
  the name will be empty).  The first name provided in this manner will be
  used.
* :py:attr:`~UserTaskStatus.is_container` is ``True``.
* :py:attr:`~UserTaskStatus.task_class` is "celery.chain".
* :py:attr:`~UserTaskStatus.total_steps` and
  :py:attr:`~UserTaskStatus.completed_steps` are kept up to date as the sum of
  those fields in all the child tasks.
* :py:attr:`~UserTaskStatus.state` is "In Progress" while any of the child
  tasks are being executed or retried (unless one of them uses
  :py:meth:`UserTaskStatus.set_state` to set a custom state, in which case
  that will propagate to the parent as well).

A failure in one of the child tasks set the parent's state to "Failed",
and successful completion of the final task in the chain will set the parent's
state to "Succeeded" as well.

Here's a typical example of creating a chain with status tracking:

.. code-block:: python

   from celery import chain
   from my_app.tasks import user_task_1, user_task_2, user_task_3

   # Argument preparation omitted

   name = 'Prepare report for {}'.format(arg1)
   chain(user_task_1.si(arg1, user_task_name=name), user_task_2.si(arg1), user_task_3.si(arg2))

Groups
------

A :py:class:`~celery.group` is a set of Celery tasks which can be run in
parallel.  (Whether or not they actually run in parallel depends on the
number of tasks in the group, the number of worker processes in use, and
how busy those workers are processing other tasks.)  ``django-user-tasks``
handles groups much as it handles chains, creating a parent
:py:class:`UserTaskStatus` record to represent the group as a whole and
setting it as the parent of each contained subclass of
:py:class:`UserTaskMixin`.  Most of what was said above for the status
records involved in a chain also applies for groups, with the following
exceptions:

* :py:attr:`~UserTaskStatus.task_class` is "celery.group" for the parent
  status record.
* Calling :py:meth:`UserTaskStatus.set_state` on a child task does not
  affect the status of the group (because it contains multiple tasks which
  could be in different states at the same time).
* :py:attr:`~UserTaskStatus.state` is set to "Succeeded" when all of the
  child tasks have succeeded.

The code for creating a group is almost identical to that for creating a
chain:

.. code-block:: python

   from celery import group
   from my_app.tasks import user_task_1, user_task_2, user_task_3

   # Argument preparation omitted

   name = 'Prepare report for {}'.format(arg1)
   group(user_task_1.si(arg1, user_task_name=name), user_task_2.si(arg1), user_task_3.si(arg2))

Chords
------

A :py:class:`~celery.chord` is essentially a common special case of nesting a
group in a chain.  It consists of a "header" of one or more tasks which can be
executed concurrently, followed by a "body" task which is to be started only
after all of the tasks in the header have completed.  ``django-user-tasks``
essentially treats it like a chain, with the following differences:

* :py:attr:`~UserTaskStatus.task_class` is "celery.chord" for the parent
  status record.
* Another status record with "celery.group" as the
  :py:attr:`~UserTaskStatus.task_class` is created as a child of the chord
  status and parent of the header tasks.
* Calling :py:meth:`UserTaskStatus.set_state` on the body task propagates to
  the parent status, but calling it for a header task does not (for the same
  reason given above for groups).
* :py:attr:`~UserTaskStatus.state` is set to "Succeeded" when the body task
  succeeds.

An example of creating a chord with status tracking:

.. code-block:: python

   from celery import chord
   from my_app.tasks import user_task_1, user_task_2, user_task_3

   # Argument preparation omitted

   name = 'Prepare report for {}'.format(arg1)
   chord([user_task_1.si(arg1, user_task_name=name), user_task_2.si(arg1)])(user_task_3.si(arg2))


Nested Groupings
----------------

Celery supports nesting chains, groups, and chords; you can have a group of
tasks of which one or more are actually chains of other tasks, etc.  While
such nested constructs can probably be correctly supported in
``django-user-tasks``, they haven't been explicitly tested yet as they seem
to be pretty rarely used in practice.
