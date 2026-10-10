"""
REST API serialization classes.
"""

from rest_framework import serializers

from .models import UserTaskArtifact, UserTaskStatus


class StatusSerializer(serializers.HyperlinkedModelSerializer):
    """
    REST API serializer for the UserTaskStatus model.
    """

    artifacts = serializers.HyperlinkedRelatedField(many=True, read_only=True, view_name='usertaskartifact-detail',
                                                    lookup_field='uuid')

    class Meta:
        """
        Status serializer settings.
        """

        model = UserTaskStatus
        fields = (
            'name', 'state', 'state_text', 'completed_steps', 'total_steps', 'attempts', 'created', 'modified',
            'artifacts'
        )


class ArtifactSerializer(serializers.HyperlinkedModelSerializer):
    """
    REST API serializer for the UserTaskArtifact model.
    """

    file = serializers.SerializerMethodField()

    class Meta:
        """
        Artifact serializer settings.
        """

        model = UserTaskArtifact
        fields = ('name', 'created', 'modified', 'status', 'file', 'text', 'url')
        extra_kwargs = {
            'status': {'lookup_field': 'uuid'},
        }

    def get_file(self, obj):
        """
        Get the URL of the artifact's associated file data.

        Arguments:
            obj (UserTaskArtifact): The artifact being serialized

        Returns:
            six.text_type: The URL of the artifact's file field (empty if there isn't one)

        """
        if not obj.file:
            return ''
        return obj.file.url
