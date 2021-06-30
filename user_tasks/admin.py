"""
Django admin configuration for the ``django-user-tasks`` models.
"""

from django.contrib import admin

from .models import UserTaskArtifact, UserTaskStatus


class UserTaskArtifactAdmin(admin.ModelAdmin):
    """
    Configuration for UserTaskArtifact admin panel.
    """

    list_display = ('created', 'uuid', 'status', 'name', 'text')
    list_filter = ('name',)
    ordering = ('-created',)
    search_fields = ('uuid', 'name', 'text')
    raw_id_fields = ('status',)


class UserTaskStatusAdmin(admin.ModelAdmin):
    """
    Configuration for UserTaskStatus admin panel.
    """

    list_display = ('created', 'uuid', 'state', 'user', 'name')
    list_filter = ('state',)
    ordering = ('-created',)
    search_fields = (
        'uuid', 'task_id', 'task_class', 'name', 'user__username', 'user__email'
    )
    readonly_fields = ('parent', )


admin.site.register(UserTaskArtifact, UserTaskArtifactAdmin)
admin.site.register(UserTaskStatus, UserTaskStatusAdmin)
