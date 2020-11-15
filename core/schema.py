import graphene
from core.mutations import *

class Mutation(graphene.ObjectType):
    signup = SignupMutation.Field()
    login = LoginMutation.Field()
    refresh_token = RefreshMutation.Field()

    update_user = UpdateUserMutation.Field()
    update_password = UpdatePasswordMutation.Field()
    delete_user = DeleteUserMutation.Field()

schema = graphene.Schema(mutation=Mutation)