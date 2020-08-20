"""
Database models for user_tasks.
"""

import logging
from uuid import uuid4

from celery import current_app

from django.conf import settings as django_settings
from django.core.validators import URLValidator
from django.db import models, transaction
from django.db.models import Q
from django.db.models.expressions import F
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _

from model_utils.models import TimeStampedModel

from user_tasks import user_task_stopped

from .conf import settings
from .exceptions import TaskCanceledException

LOGGER = logging.getLogger(__name__)

# The pylint "disable=no-member" comments are needed because of the 'self' argument to the parent field definition.
# See https://github.com/landscapeio/pylint-django/issues/35 for more details


class UserTaskStatus(TimeStampedModel):
    """
    The current status of an asynchronous task running on behalf of a particular user.

    The methods of this class should generally not be run as part of larger
    transactions.  If they are, some deadlocks and race conditions become
    possible.
    """

    PENDING = 'Pending'
    IN_PROGRESS = 'In Progress'
    SUCCEEDED = 'Succeeded'
    FAILED = 'Failed'
    CANCELED = 'Canceled'
    RETRYING = 'Retrying'

    STATE_TRANSLATIONS = {
        PENDING: _('Pending'),
        IN_PROGRESS: _('In Progress'),
        SUCCEEDED: _('Succeeded'),
        FAILED: _('Failed'),
        CANCELED: _('Canceled'),
        RETRYING: _('Retrying'),
    }

    uuid = models.UUIDField(default=uuid4, unique=True, editable=False, help_text='Unique ID for use in APIs')
    user = models.ForeignKey(
        django_settings.AUTH_USER_MODEL,
        help_text='The user who triggered the task',
        on_delete=models.CASCADE,
    )
    # Auto-generated Celery task IDs will always be 36 characters, but longer custom ones can be specified
    task_id = models.CharField(max_length=128, unique=True, db_index=True,
                               help_text='UUID of the associated Celery task')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, default=None,
                               help_text='Status of the containing task grouping (if any)')
    is_container = models.BooleanField(default=False,
                                       help_text='True if this status corresponds to a container of multiple tasks')
    task_class = models.CharField(max_length=128, help_text='Fully qualified class name of the task being performed')
    name = models.CharField(max_length=255, help_text='A name for this task which the triggering user will understand')
    state = models.CharField(max_length=128, default=PENDING)
    completed_steps = models.PositiveSmallIntegerField(default=0)
    total_steps = models.PositiveSmallIntegerField()
    attempts = models.PositiveSmallIntegerField(default=1, help_text='How many times has execution been attempted?')

    class Meta:
        """
        Additional configuration for the UserTaskStatus model.
        """

        verbose_name_plural = 'user task statuses'

    def start(self):
        """
        Mark the task as having been started (as opposed to waiting for an available worker), and save it.
        """
        if self.state == UserTaskStatus.CANCELED and not self.is_container:
            raise TaskCanceledException
        self.state = UserTaskStatus.IN_PROGRESS
        self.save(update_fields={'state', 'modified'})
        if self.parent_id:
            with transaction.atomic():
                parent = UserTaskStatus.objects.select_for_update().get(pk=self.parent_id)
                if parent.state in (UserTaskStatus.PENDING, UserTaskStatus.RETRYING):
                    parent.start()

    def increment_completed_steps(self, steps=1):
        """
        Increase the value of :py:attr:`completed_steps` by the given number and save, then check for cancellation.

        If cancellation of the task has been requested, a TaskCanceledException
        will be raised to abort execution.  If any special cleanup is required,
        this exception should be caught and handled appropriately.

        This method should be called often enough to provide a useful
        indication of progress, but not so often as to cause undue burden on
        the database.
        """
        UserTaskStatus.objects.filter(pk=self.id).update(completed_steps=F('completed_steps') + steps,
                                                         modified=now())
        self.refresh_from_db(fields={'completed_steps', 'modified', 'state'})
        if self.parent:
            self.parent.increment_completed_steps(steps)  # pylint: disable=no-member
        # Was a cancellation command recently sent?
        if self.state == self.CANCELED and not self.is_container:
            raise TaskCanceledException

    def increment_total_steps(self, steps):
        """Increase the value of :py:attr:`total_steps` by the given number and save."""
        # Assume that other processes may be making concurrent changes
        UserTaskStatus.objects.filter(pk=self.id).update(total_steps=F('total_steps') + steps, modified=now())
        self.refresh_from_db(fields={'total_steps', 'modified'})
        if self.parent:
            self.parent.increment_total_steps(steps)  # pylint: disable=no-member

    def cancel(self):
        """
        Cancel the associated task if it hasn't already finished running.
        """
        if self.is_container:
            children = UserTaskStatus.objects.filter(parent=self)
            for child in children:
                child.cancel()
        elif self.state in (UserTaskStatus.PENDING, UserTaskStatus.RETRYING):
            current_app.control.revoke(self.task_id)
            user_task_stopped.send_robust(UserTaskStatus, status=self)
        with transaction.atomic():
            status = UserTaskStatus.objects.select_for_update().get(pk=self.id)
            if status.state in (UserTaskStatus.CANCELED, UserTaskStatus.FAILED, UserTaskStatus.SUCCEEDED):
                return
            status.state = UserTaskStatus.CANCELED
            status.save(update_fields={'state', 'modified'})
            self.state = status.state
            self.modified = status.modified

    def fail(self, message):
        """
        Mark the task as having failed for the given reason, and save it.

        The message will be available as the :py:attr:`UserTaskArtifact.text`
        field of a UserTaskArtifact with name "Error".  There may be more than
        one such artifact for a single UserTaskStatus, especially if it
        represents a container for multiple parallel tasks.
        """
        with transaction.atomic():
            UserTaskArtifact.objects.create(status=self, name='Error', text=message)
            self.state = UserTaskStatus.FAILED
            self.save(update_fields={'state', 'modified'})
        if self.parent:
            self.parent.fail(message)  # pylint: disable=no-member

    def retry(self):
        """
        Update the status to reflect that a problem was encountered and the task will be retried later.
        """
        # Note that a retry does not affect the state of a containing task
        # grouping; it's effectively still in progress
        self.attempts += 1
        self.state = UserTaskStatus.RETRYING
        self.save(update_fields={'attempts', 'state', 'modified'})

    def set_name(self, name):
        """
        Give the specified name to this status and all of its ancestors.
        """
        self.name = name
        self.save(update_fields={'name', 'modified'})
        if self.parent:
            self.parent.set_name(name)  # pylint: disable=no-member

    def set_state(self, custom_state):
        """
        Set the state to a custom in-progress value.

        This can be done to indicate which stage of a long task is currently
        being executed, like "Sending email messages".
        """
        with transaction.atomic():
            status = UserTaskStatus.objects.select_for_update().get(pk=self.id)
            if status.state == UserTaskStatus.CANCELED and not self.is_container:
                raise TaskCanceledException
            status.state = custom_state
            status.save(update_fields={'state', 'modified'})
            self.state = status.state
            self.modified = status.modified
        if self.parent and self.parent.task_class != 'celery.group':  # pylint: disable=no-member
            self.parent.set_state(custom_state)  # pylint: disable=no-member

    @property
    def state_text(self):
        """
        Get the translation into the current language of the current state of this status instance.
        """
        return self.STATE_TRANSLATIONS.get(self.state, self.state)

    def succeed(self):
        """
        Mark the task as having finished successfully and save it.
        """
        if self.completed_steps < self.total_steps:
            self.increment_completed_steps(self.total_steps - self.completed_steps)
        self.state = UserTaskStatus.SUCCEEDED
        self.save(update_fields={'state', 'modified'})
        if self.parent_id:
            query = UserTaskStatus.objects.filter(~Q(state=UserTaskStatus.SUCCEEDED), parent__pk=self.parent_id)
            if not query.exists():
                self.parent.succeed()  # pylint: disable=no-member

    def __str__(self):
        """
        Get a string representation of this task.
        """
        return '<UserTaskStatus: {}>'.format(self.name)


class UserTaskArtifact(TimeStampedModel):
    """
    An artifact (or error message) generated for a user by an asynchronous task.

    May be a file, a URL, or text stored directly in the database table.
    """

    uuid = models.UUIDField(default=uuid4, unique=True, editable=False, help_text='Unique ID for use in APIs')
    status = models.ForeignKey(UserTaskStatus, on_delete=models.CASCADE, related_name='artifacts')
    name = models.CharField(max_length=255, default='Output',
                            help_text='Distinguishes between multiple artifact types for the same task')
    file = models.FileField(null=True, blank=True, storage=settings.USER_TASKS_ARTIFACT_STORAGE,
                            upload_to='user_tasks/%Y/%m/%d/')
    url = models.TextField(blank=True, validators=[URLValidator()])
    text = models.TextField(blank=True)

    def __str__(self):
        """
        Get a string representation of this artifact.
        """
        if self.file:
            content = self.file.name
        elif self.url:
            content = self.url
        elif len(self.text) > 50:
            content = self.text[:47] + '...'
        else:
            content = self.text
        return '<UserTaskArtifact: ({}) {}>'.format(self.name, content)
