import json
from graphql.error import GraphQLLocatedError, GraphQLError
from graphene_file_upload.django import FileUploadGraphQLView
from graphene_django.views import GraphQLView
import django.conf
from django.urls import path, include
from django.conf.urls.static import static
from core.data import return_data

class ReadableErrorGraphQLView(FileUploadGraphQLView):
    """A custom GraphQLView which stops Python error messages being sent to
    the user unless they were explicitly raised."""

    @staticmethod
    def format_error(error):
        if isinstance(error, GraphQLLocatedError):
            try:
                error_dict = json.loads(str(error))
            except: 
                return GraphQLView.format_error(GraphQLError("Resolver error"))
        return GraphQLView.format_error(error)

urlpatterns = [
    path("graphql", ReadableErrorGraphQLView.as_view()),
    path("peka/", include("peka.urls")),
    path("data/<int:id>/<str:name>", return_data)
]

if django.conf.settings.SERVE_FILES:
    urlpatterns += static(
        django.conf.settings.MEDIA_URL,
        document_root=django.conf.settings.MEDIA_ROOT
    )