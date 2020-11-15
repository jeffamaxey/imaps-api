import time
import json
import graphene
from graphql import GraphQLError
from core.models import User
from core.forms import *
from core.arguments import create_mutation_arguments

class SignupMutation(graphene.Mutation):

    Arguments = create_mutation_arguments(SignupForm)

    access_token = graphene.String()

    def mutate(self, info, **kwargs):
        form = SignupForm(kwargs)
        if form.is_valid():
            form.instance.last_login = time.time()
            form.save()
            info.context.refresh_token = form.instance.make_jwt()
            return SignupMutation(access_token=form.instance.make_jwt())
        raise GraphQLError(json.dumps(form.errors))