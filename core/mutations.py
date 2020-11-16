import time
import json
import graphene
from graphql import GraphQLError
from django.contrib.auth.hashers import check_password
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
            info.context.refresh_token = form.instance.make_refresh_jwt()
            return SignupMutation(access_token=form.instance.make_access_jwt())
        raise GraphQLError(json.dumps(form.errors))



class LoginMutation(graphene.Mutation):

    class Arguments:
        username = graphene.String()
        password = graphene.String()
    
    access_token = graphene.String()

    def mutate(self, info, **kwargs):
        user = User.objects.filter(username=kwargs["username"]).first()
        if user:
            if check_password(kwargs["password"], user.password):
                info.context.refresh_token = user.make_refresh_jwt()
                user.last_login = time.time()
                user.save()
                return LoginMutation(access_token=user.make_access_jwt())
        raise GraphQLError(json.dumps({"username": "Invalid credentials"}))



class RefreshMutation(graphene.Mutation):

    access_token = graphene.String()

    def mutate(self, info, **kwargs):
        token = info.context.COOKIES.get("refresh_token")
        if not token:
            raise GraphQLError(json.dumps({"token": "No refresh token supplied"}))
        user = User.from_token(token)
        if user:
            info.context.refresh_token = user.make_refresh_jwt()
            return RefreshMutation(access_token=user.make_access_jwt())
        raise GraphQLError(json.dumps({"token": "Refresh token not valid"}))



class UpdateUserMutation(graphene.Mutation):

    Arguments = create_mutation_arguments(UpdateUserForm)
    
    user = graphene.Field("core.queries.UserType")

    def mutate(self, info, **kwargs):
        if not info.context.user:
            raise GraphQLError(json.dumps({"error": "Not authorized"}))
        form = UpdateUserForm(kwargs, instance=info.context.user)
        if form.is_valid():
            form.save()
            return UpdateUserMutation(user=form.instance)
        raise GraphQLError(json.dumps(form.errors))



class UpdatePasswordMutation(graphene.Mutation):

    Arguments = create_mutation_arguments(UpdatePasswordForm)
    
    success = graphene.Boolean()

    def mutate(self, info, **kwargs):
        if not info.context.user:
            raise GraphQLError(json.dumps({"error": "Not authorized"}))
        form = UpdatePasswordForm(kwargs, instance=info.context.user)
        if form.is_valid():
            form.save()
            return UpdatePasswordMutation(success=True)
        raise GraphQLError(json.dumps(form.errors))



class DeleteUserMutation(graphene.Mutation):

    class Arguments:
        password = graphene.String(required=True)

    success = graphene.Boolean()

    def mutate(self, info, **kwargs):
        user = info.context.user
        if user:
            if check_password(kwargs["password"], user.password):
                user.delete()
                return DeleteUserMutation(success=True)
            raise GraphQLError(json.dumps({"username": "Invalid credentials"}))
        raise GraphQLError(json.dumps({"username": "Invalid or missing token"}))



class CreateGroupMutation(graphene.Mutation):

    Arguments = create_mutation_arguments(GroupForm)
    
    group = graphene.Field("core.queries.GroupType")

    def mutate(self, info, **kwargs):
        if not info.context.user:
            raise GraphQLError(json.dumps({"error": "Not authorized"}))
        form = GroupForm(kwargs)
        if form.is_valid():
            form.save()
            form.instance.users.add(info.context.user)
            form.instance.admins.add(info.context.user)
            return CreateGroupMutation(group=form.instance)
        raise GraphQLError(json.dumps(form.errors))



class UpdateGroupMutation(graphene.Mutation):

    Arguments = create_mutation_arguments(GroupForm, edit=True)
    
    group = graphene.Field("core.queries.GroupType")

    def mutate(self, info, **kwargs):
        if not info.context.user:
            raise GraphQLError(json.dumps({"error": "Not authorized"}))
        group = Group.objects.filter(id=kwargs["id"])
        if not group: raise GraphQLError('{"group": ["Does not exist"]}')
        if not info.context.user.admin_groups.filter(id=kwargs["id"]):
            raise GraphQLError('{"group": ["Not an admin"]}')
        form = GroupForm(kwargs, instance=group.first())
        if form.is_valid():
            form.save()
            return UpdateGroupMutation(group=form.instance)
        raise GraphQLError(json.dumps(form.errors))