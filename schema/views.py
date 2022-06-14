"""
Views for rendering REST API schema documents.
"""
import logging
import os

from rest_framework import response, schemas
from rest_framework.decorators import api_view, renderer_classes
from rest_framework_swagger.renderers import OpenAPIRenderer, SwaggerUIRenderer

LOGGER = logging.getLogger(__name__)


class ConditionalOpenAPIRenderer(OpenAPIRenderer):
    """
    Open API JSON renderer which uses the ``SWAGGER_JSON_PATH`` environment variable when set.

    This allows Swagger UI to use the hand-customized ``swagger.json`` file
    provided with the documentation when ``make swagger-ui`` is run.
    """

    def render(self, data, accepted_media_type=None, renderer_context=None):
        """
        Render the appropriate Open API JSON file.
        """
        if 'SWAGGER_JSON_PATH' in os.environ:
            with open(os.environ['SWAGGER_JSON_PATH'], 'rb') as f:
                return f.read()
        else:
            return super().render(data, accepted_media_type, renderer_context)


@api_view()
@renderer_classes([ConditionalOpenAPIRenderer, SwaggerUIRenderer])
def swagger(request):
    """
    Render Swagger UI and the underlying Open API schema JSON file.
    """
    generator = schemas.SchemaGenerator(title='django-user-tasks REST API')
    return response.Response(generator.get_schema())
