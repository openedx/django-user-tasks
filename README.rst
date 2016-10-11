django-user-tasks
=================

.. image:: https://img.shields.io/pypi/v/django-user-tasks.svg
    :target: https://pypi.python.org/pypi/django-user-tasks/
    :alt: PyPI

.. image:: https://travis-ci.org/edx/django-user-tasks.svg?branch=master
    :target: https://travis-ci.org/edx/django-user-tasks
    :alt: Travis

.. image:: http://codecov.io/github/edx/django-user-tasks/coverage.svg?branch=master
    :target: http://codecov.io/github/edx/django-user-tasks?branch=master
    :alt: Codecov

.. image:: http://django-user-tasks.readthedocs.io/en/latest/?badge=latest
    :target: http://django-user-tasks.readthedocs.io/en/latest/
    :alt: Documentation

.. image:: https://img.shields.io/pypi/pyversions/django-user-tasks.svg
    :target: https://pypi.python.org/pypi/django-user-tasks/
    :alt: Supported Python versions

.. image:: https://img.shields.io/github/license/edx/django-user-tasks.svg
    :target: https://github.com/edx/django-user-tasks/blob/master/LICENSE.txt
    :alt: License

django-user-tasks is a reusable Django application for managing user-triggered
asynchronous tasks.  It provides a status page for each such task, which
includes a meaningful progress indicator if the task is currently being
executed and provides any appropriate text and/or links for output once the
task is complete.

In Open edX, such tasks include operations such as exporting or importing a
course, sending an email to all the students in a course, uploading a video,
and other tasks which often take too long to perform during a single web
request (as outlined in `OEP-3`_).  However, this has been written with the
intention of being useful in a variety of Django projects outside the Open edX
platform as well.

Note that this library was created as a consolidation of lessons learned from
implementing such tasks in various parts of the Open edX code base.  They
don't yet all use this library, but the plan is to over time refactor many of
them to do so.

.. _OEP-3: https://open-edx-proposals.readthedocs.io/en/latest/oeps/oep-0003.html

Overview
--------

django-user-tasks is currently a wrapper for `Celery`_ (although the hope is
that it could also be extended to also support `channels`_ and other
asynchronous task queues).  By extending the provided ``UserTask`` class (or
adding ``UserTaskMixin`` to an existing Task subclass) and providing a
``user_id`` task argument, the task's status is stored in a database table
separate from the Celery broker and result store.  This ``UserTaskStatus``
model allows for full database queries of the tasks that users are most likely
to care about while not imposing any restrictions on the Celery configuration
most appropriate for the site's overall needs for asynchronous task
processing.

Most of the status updating is handled automatically via Celery's `signals`_
mechanism, but it can be enhanced by:

* Overriding the ``UserTaskMixin`` methods such as ``generate_name`` and
  ``calculate_total_steps`` for particular types of tasks
* Calling some of the ``UserTaskStatus`` methods like
  ``increment_completed_steps`` and ``set_state`` from the task implementation
* Saving task output as instances of the ``UserTaskArtifact`` model

.. _Celery: http://www.celeryproject.org/
.. _channels: https://channels.readthedocs.io/en/latest/
.. _signals: http://docs.celeryproject.org/en/latest/userguide/signals.html

Documentation
-------------

The full documentation is at https://django-user-tasks.readthedocs.org.

License
-------

The code in this repository is licensed under the Apache Software License 2.0 unless
otherwise noted.

Please see ``LICENSE.txt`` for details.

How To Contribute
-----------------

Contributions are very welcome.

Please read `How To Contribute <https://github.com/edx/edx-platform/blob/master/CONTRIBUTING.rst>`_ for details.

Even though they were written with ``edx-platform`` in mind, the guidelines
should be followed for Open edX code in general.

Reporting Security Issues
-------------------------

Please do not report security issues in public. Please email security@edx.org.

Getting Help
------------

Have a question about this repository, or about Open edX in general?  Please
refer to this `list of resources`_ if you need any assistance.

.. _list of resources: https://open.edx.org/getting-help
