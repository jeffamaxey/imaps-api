import graphene
from core.mutations import *

class Mutation(graphene.ObjectType):
    signup = SignupMutation.Field()
    login = LoginMutation.Field()
    refresh_token = RefreshMutation.Field()

schema = graphene.Schema(mutation=Mutation)