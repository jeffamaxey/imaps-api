import graphene
from core.mutations import *

class Mutation(graphene.ObjectType):
    signup = SignupMutation.Field()

schema = graphene.Schema(mutation=Mutation)