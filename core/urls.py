import json
from graphql.error import GraphQLLocatedError, GraphQLError
from graphene_django.views import GraphQLView
from django.urls import path

class ReadableErrorGraphQLView(GraphQLView):
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
]