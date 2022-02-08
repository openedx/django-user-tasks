Change Log
----------

..
   All enhancements and patches to django-user-tasks will be documented
   in this file.  It adheres to the structure of http://keepachangelog.com/ ,
   but in reStructuredText instead of Markdown (for ease of incorporation into
   Sphinx documentation and the PyPI description).

   This project adheres to Semantic Versioning (http://semver.org/).

.. There should always be an "Unreleased" section for changes pending release.

Unreleased
~~~~~~~~~~

Removed
+++++++

* Removed Python 3.5 support.

Chore
+++++

* Upgraded celery to latest 5.x version.

[2.2.0] - 2022-01-26
~~~~~~~~~~~~~~~~~~~~

Removed
+++++++

* Removed Django22,30,31 support.

Added
+++++

* Added Django40 support in CI

[2.1.0] - 2021-07-07
~~~~~~~~~~~~~~~~~~~~

Added
+++++

* Support for django3.0, 3.1 and 3.2

[2.0.3] - 2021-06-08
~~~~~~~~~~~~~~~~~~~~

Changed
+++++++

* Fixed django admin timeout issue.

[2.0.2] - 2021-05-28
~~~~~~~~~~~~~~~~~~~~

Changed
+++++++

* Fixed minor issue. If links key is not available assign empty list. Added logs.


[2.0.1] - 2021-05-28
~~~~~~~~~~~~~~~~~~~~

Added
+++++++

* Added celery5.0 testing with tox. Update the import task command compatible with both celery 4.4.7 and celery5.0.


[2.0.0] - 2021-01-20
~~~~~~~~~~~~~~~~~~~~

Removed
+++++++

* Removed python3.5 support.


[1.3.2] - 2020-12-17
~~~~~~~~~~~~~~~~~~~~

Changed
+++++++

* Added celery 5.0 testing using tox. Fix pylint warnings. Update the code accordingly.


[1.3.2] - 2020-12-17
~~~~~~~~~~~~~~~~~~~~

Changed
+++++++

* Updated the deprecated celery import class. New import is compatible with 4.4.7 also.


[1.3.1] - 2020-11-23
~~~~~~~~~~~~~~~~~~~~

Added
+++++

* Added support for Django REST Framework 3.10.x through 3.12.x

[1.3.0] - 2020-08-25
~~~~~~~~~~~~~~~~~~~~

Added
+++++

* Added support for celery 4

[1.2.0] - 2020-08-20
~~~~~~~~~~~~~~~~~~~~

Removed
+++++++

* Removed code related to Python 2


[1.1.0] - 2020-05-07
~~~~~~~~~~~~~~~~~~~~

Added
+++++++

* Added support for python 3.8

Removed
+++++++

* Dropped support for Django < 2.2

[1.0.0] - 2020-03-18
~~~~~~~~~~~~~~~~~~~~

Removed
+++++++

* Dropped Python 2.7 support

[0.3.0] - 2019-12-15
~~~~~~~~~~~~~~~~~~~~

Added
+++++

* Added support for Django 2.2

[0.2.1] - 2019-09-25
~~~~~~~~~~~~~~~~~~~~

Changed
+++++++

* `start_user_task` should only close obsolete connections if the current connection is NOT in an atomic block
  (which fixes errors on devstack studio/course-publishing).

[0.2.0] - 2019-08-30
~~~~~~~~~~~~~~~~~~~~

Changed
+++++++

* Have the `start_user_task` receiver close obsolete connections before starting the task.


[0.1.9] - 2019-08-27
~~~~~~~~~~~~~~~~~~~~

Changed
+++++++

* Fix issue with `UserTaskArtifactAdmin` and `UserTaskStatusAdmin` where `ordering` attribute must be a tuple or list.


[0.1.8] - 2019-08-22
~~~~~~~~~~~~~~~~~~~~

Changed
+++++++

* Improve list display for `ModelAdmin`.


[0.1.7] - 2019-05-29
~~~~~~~~~~~~~~~~~~~~

Changed
+++++++

* Make ``UserTaskArtifact.url`` a ``TextField`` with a ``URLValidator``
  instead of a ``URLField``.


[0.1.6] - 2019-05-29
~~~~~~~~~~~~~~~~~~~~

Changed
+++++++

* Upgrade requirements.
* Change ``max_length`` of ``UserTaskArtifact.url`` from 200 to 512.


[0.1.5] - 2017-08-03
~~~~~~~~~~~~~~~~~~~~

Changed
+++++++

* Added testing/support for Django 1.11.

[0.1.4] - 2017-01-30
~~~~~~~~~~~~~~~~~~~~

Changed
+++++++

* Slightly improved handling of tasks which start before their status records
  are committed (due to database transactions).  Also documented how to avoid
  this problem in the first place.

[0.1.3] - 2017-01-03
~~~~~~~~~~~~~~~~~~~~

Changed
+++++++

* Tasks which were explicitly canceled, failed, or retried no longer have
  their status changed to ``Succeeded`` just because the task exited cleanly.
* Celery tasks which fail to import cleanly by name (because they use a custom
  name which isn't actually the fully qualified task name) are now just ignored
  in the ``before_task_publish`` signal handler.

[0.1.2] - 2016-12-05
~~~~~~~~~~~~~~~~~~~~

Changed
+++++++

* Add a migration to explicitly reference the setting for artifact file storage.
  This setting is likely to vary between installations, but doesn't affect the
  generated database schema.  This change should prevent ``makemigrations``
  from creating a new migration whenever the setting value changes.

[0.1.1] - 2016-10-11
~~~~~~~~~~~~~~~~~~~~

Changed
+++++++

* Fix Travis configuration for PyPI deployments.
* Switch from the Read the Docs Sphinx theme to the Open edX one for documentation.


[0.1.0] - 2016-10-07
~~~~~~~~~~~~~~~~~~~~

Added
+++++

* First attempt to release on PyPI.
