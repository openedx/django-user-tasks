Getting Started
===============

These are the typical steps to add ``django-user-tasks`` to a site and use it
for a single type of task:

1. Install ``django-user-tasks`` (typically via
   ``pip install django-user-tasks``, but use whatever mechanism you've chosen
   for dependency management).
2. Add ``django-user-tasks`` and ``rest_framework`` to the ``INSTALLED_APPS`` Django setting.
3. Run migrations to create the required database tables.
4. Create a subclass of :py:class:`user_tasks.tasks.UserTask` and override one or
   two of its methods.
5. Define a task which uses the class you just created.
6. Call the task as per the Celery documentation (``task_name.delay()``, etc.)

A minimal ``tasks.py`` in your application might look something like this:

.. code-block:: python

   from celery import shared_task
   from user_tasks.models import UserTaskArtifact
   from user_tasks.tasks import UserTask
   from my_app.models import Course


   @shared_task(base=UserTask, bind=True)
   def export_task(self, user_id, course_id):
       course = Course.objects.get(pk=arguments_dict['course_id'])
       output = ''
       for section in course.sections():
           output += section.export()
       UserTaskArtifact.objects.create(status=self.status, text=output)

This implementation has some limitations on the quality of data you can see
in the interface, though.  Every task of this type would appear in the UI
with the name "export_task", the progress bar would always be either empty
or full, and the displayed status during execution would just be
"In Progress".  This might be adequate for a relatively quick task that
doesn't take any meaningful parameters, but these points can be improved
with a few code changes:

.. code-block:: python

   from celery import shared_task
   from user_tasks.models import UserTaskArtifact
   from user_tasks.tasks import UserTask
   from my_app.models import Course


   class ExportTask(UserTask):

       @classmethod
       def generate_name(cls, arguments_dict):
           course = Course.objects.get(pk=arguments_dict['course_id'])
           return 'Export of {}'.format(course.name)

       @staticmethod
       def calculate_total_steps(arguments_dict):
           course = Course.objects.get(pk=arguments_dict['course_id'])
           return course.sections.count()


   @shared_task(base=ExportTask, bind=True)
   def export_task(self, user_id, course_id):
       course = Course.objects.get(pk=arguments_dict['course_id'])
       output = ''
       for section in course.sections():
           self.status.set_state('Exporting {}'.format(section.name))
           output += section.export()
           self.status.increment_completed_steps()
       UserTaskArtifact.objects.create(status=self.status, text=output)

Now the name of the task includes the name of the course being exported,
there's an indication of how far along execution of the task has progressed,
and while in progress the status reflects the name of the section currently
being exported.

URL Configuration
-----------------

Out of the box, ``django-user-tasks`` provides a ``urls`` module containing a URLconf which places the REST API
endpoints under ``tasks/`` and ``artifacts/``.  You can include ``user_tasks.urls.urlpatterns`` in your
service's overall URL configuration, or create a custom configuration which uses paths of your choice.  For example:

.. code-block:: python

    from rest_framework.routers import SimpleRouter
    from user_tasks.views import ArtifactViewSet, StatusViewSet

    ROUTER = SimpleRouter()
    ROUTER.register(r'user_task_artifacts', ArtifactViewSet, base_name='usertaskartifact')
    ROUTER.register(r'user_tasks/', StatusViewSet, base_name='usertaskstatus')

    urlpatterns = ROUTER.urls

Task Status Signal
------------------

When a subclass of :py:class:`user_tasks.tasks.UserTaskMixin` reaches any end state (``Canceled``, ``Failed``, or
``Succeeded``), a ``user_tasks.user_task_stopped`` signal is sent.  Listeners can use this signal to notify users of
the status change, log relevant statistics, etc.  The signal's ``sender`` is the :py:class:`UserTaskStatus` class,
and its ``status`` argument is the instance of that class for which the signal was sent.

Note on Database Transactions
-----------------------------

If the code that triggers a :py:class:`user_tasks.tasks.UserTaskMixin` is
contained in a database transaction, note that the Celery task may start
before the new UserTaskStatus record has been committed to the database.
``django-user-tasks`` tries to compensate for this, but it can still lead to
errors in some pathological timing scenarios, so try to avoid creating such
tasks during long transactions.  On Django 1.10 and later,
`transaction.on_commit`_ can make this easier.

Furthermore, Django used to default to
`wrapping each request in a database transaction`_.  While this is no longer
the default behavior, many older applications (or newer ones with specialized
needs) are still using this atomic requests feature.  You should generally
either use `transaction.on_commit`_ or the `transaction.non_atomic_requests`_
decorator for views creating user tasks in applications with this setting enabled.

.. _transaction.on_commit: https://docs.djangoproject.com/en/1.10/topics/db/transactions/#django.db.transaction.on_commit
.. _wrapping each request in a database transaction: https://docs.djangoproject.com/en/1.11/topics/db/transactions/#tying-transactions-to-http-requests
.. _transaction.non_atomic_requests: https://docs.djangoproject.com/en/1.11/topics/db/transactions/#django.db.transaction.non_atomic_requests
