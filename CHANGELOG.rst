Change Log
----------

..
   All enhancements and patches to cookiecutter-django-app will be documented
   in this file.  It adheres to the structure of http://keepachangelog.com/ ,
   but in reStructuredText instead of Markdown (for ease of incorporation into
   Sphinx documentation and the PyPI description).
   
   This project adheres to Semantic Versioning (http://semver.org/).

.. There should always be an "Unreleased" section for changes pending release.

Unreleased
~~~~~~~~~~

[0.1.3] - 2017-01-03
~~~~~~~~~~~~~~~~~~~~

Changed
-------

* Tasks which were explicitly canceled, failed, or retried no longer have
  their status changed to ``Succeeded`` just because the task exited cleanly.
* Celery tasks which fail to import cleanly by name (because they use a custom
  name which isn't actually the fully qualified task name) are now just ignored
  in the ``before_task_publish`` signal handler.

[0.1.2] - 2016-12-05
~~~~~~~~~~~~~~~~~~~~

Changed
-------

* Add a migration to explicitly reference the setting for artifact file storage.
  This setting is likely to vary between installations, but doesn't affect the
  generated database schema.  This change should prevent ``makemigrations``
  from creating a new migration whenever the setting value changes.

[0.1.1] - 2016-10-11
~~~~~~~~~~~~~~~~~~~~

Changed
_______

* Fix Travis configuration for PyPI deployments.
* Switch from the Read the Docs Sphinx theme to the Open edX one for documentation.


[0.1.0] - 2016-10-07
~~~~~~~~~~~~~~~~~~~~

Added
_____

* First attempt to release on PyPI.
