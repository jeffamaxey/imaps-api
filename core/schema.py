import graphene
from core.mutations import *

class Mutation(graphene.ObjectType):
    signup = SignupMutation.Field()
    login = LoginMutation.Field()

schema = graphene.Schema(mutation=Mutation)