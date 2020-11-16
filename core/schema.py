import graphene
from graphql import GraphQLError
from core.mutations import *

class Query(graphene.ObjectType):

    user = graphene.Field("core.queries.UserType")
    group = graphene.Field("core.queries.GroupType", id=graphene.ID(required=True))

    def resolve_user(self, info, **kwargs):
        user = info.context.user
        if not user: raise GraphQLError('{"user": "Not authorized"}')
        return info.context.user
    

    def resolve_group(self, info, **kwargs):
        try:
            return Group.objects.get(id=kwargs["id"])
        except: raise GraphQLError('{"group": "Does not exist"}')




class Mutation(graphene.ObjectType):
    signup = SignupMutation.Field()
    login = LoginMutation.Field()
    refresh_token = RefreshMutation.Field()

    update_user = UpdateUserMutation.Field()
    update_password = UpdatePasswordMutation.Field()
    delete_user = DeleteUserMutation.Field()

    create_group = CreateGroupMutation.Field()

schema = graphene.Schema(query=Query, mutation=Mutation)