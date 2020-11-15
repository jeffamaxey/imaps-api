import graphene
from graphql import GraphQLError
from core.mutations import *

class Query(graphene.ObjectType):

    user = graphene.Field("core.queries.UserType")

    def resolve_user(self, info, **kwargs):
        user = info.context.user
        if not user: raise GraphQLError('{"user": "Not authorized"}')
        return info.context.user



class Mutation(graphene.ObjectType):
    signup = SignupMutation.Field()
    login = LoginMutation.Field()
    refresh_token = RefreshMutation.Field()

    update_user = UpdateUserMutation.Field()
    update_password = UpdatePasswordMutation.Field()
    delete_user = DeleteUserMutation.Field()

schema = graphene.Schema(query=Query, mutation=Mutation)