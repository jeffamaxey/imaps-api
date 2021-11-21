import time
import json
import secrets
from django.core.exceptions import ValidationError
import graphene
from graphql import GraphQLError
from django.contrib.auth.hashers import check_password
from django.contrib.auth.password_validation import validate_password
from core.models import User, Group, UserGroupLink
from core.forms import SignupForm, UpdateUserForm, UpdatePasswordForm, UpdateUserImageForm, GroupForm
from core.email import send_welcome_email, send_reset_email, send_reset_warning_email
from core.arguments import create_mutation_arguments

class SignupMutation(graphene.Mutation):

    Arguments = create_mutation_arguments(SignupForm)

    access_token = graphene.String()
    user = graphene.Field("core.queries.UserType")

    def mutate(self, info, **kwargs):
        form = SignupForm(kwargs)
        if form.is_valid():
            form.instance.last_login = time.time()
            form.save()
            send_welcome_email(form.instance, info.context.META.get(
                "HTTP_ORIGIN", "https://imaps.goodwright.com"
            ))
            info.context.imaps_refresh_token = form.instance.make_refresh_jwt()
            info.context.user = form.instance
            return SignupMutation(
                access_token=form.instance.make_jwt(900),
                user=form.instance
            )
        raise GraphQLError(json.dumps(form.errors))



class LoginMutation(graphene.Mutation):

    class Arguments:
        username = graphene.String()
        password = graphene.String()
    
    access_token = graphene.String()
    user = graphene.Field("core.queries.UserType")

    def mutate(self, info, **kwargs):
        time.sleep(1)
        user = User.objects.filter(username=kwargs["username"]).first()
        if user:
            if check_password(kwargs["password"], user.password):
                info.context.imaps_refresh_token = user.make_jwt(31536000)
                info.context.user = user
                user.last_login = time.time()
                user.save()
                return LoginMutation(access_token=user.make_jwt(900), user=user)
        raise GraphQLError(json.dumps({"username": "Invalid credentials"}))



class LogoutMutation(graphene.Mutation):
    
    success = graphene.Boolean()

    def mutate(self, info, **kwargs):
        info.context.imaps_refresh_token = False
        return LogoutMutation(success=True)



class RequestPasswordResetMutation(graphene.Mutation):

    class Arguments:
        email = graphene.String()

    success = graphene.Boolean()

    def mutate(self, info, **kwargs):
        matches = User.objects.filter(email=kwargs["email"])
        random_token = secrets.token_hex(64)
        reset_url = info.context.META.get(
            "HTTP_ORIGIN", "https://imaps.goodwright.com"
        ) + f"/password-reset?token={random_token}"
        if matches:
            user = matches.first()
            user.password_reset_token = random_token
            user.password_reset_token_expiry = time.time() + 3600
            user.save()
            send_reset_email(user, reset_url)
        else:
            send_reset_warning_email(kwargs["email"])
        return RequestPasswordResetMutation(success=True)



class ResetPasswordMutation(graphene.Mutation):

    class Arguments:
        password = graphene.String()
        token = graphene.String()

    success = graphene.Boolean()

    def mutate(self, info, **kwargs):
        matches = User.objects.filter(password_reset_token=kwargs["token"])
        if matches:
            user = matches.first()
            if user.password_reset_token_expiry < time.time():
                raise GraphQLError(json.dumps({"token": ["Token has expired"]}))
            try:
                validate_password(kwargs["password"])
            except ValidationError as e:
                raise GraphQLError(json.dumps({"password": [str(e.error_list[0])[2:-2]]}))
            user.set_password(kwargs["password"])
            user.password_reset_token = ""
            user.password_reset_token_expiry = 0
            user.save()
            return ResetPasswordMutation(success=True)
        raise GraphQLError(json.dumps({"token": ["Token is not valid"]}))



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



class UpdateUserImageMutation(graphene.Mutation):

    Arguments = create_mutation_arguments(UpdateUserImageForm)
    
    user = graphene.Field("core.queries.UserType")

    def mutate(self, info, **kwargs):
        if not info.context.user:
            raise GraphQLError('{"user": "Not authorized"}')
        form = UpdateUserImageForm(kwargs, files=kwargs, instance=info.context.user)
        if form.is_valid():
            form.save()
            return UpdateUserImageMutation(user=form.instance)
        raise GraphQLError(json.dumps(form.errors))



class DeleteUserMutation(graphene.Mutation):

    success = graphene.Boolean()

    def mutate(self, info, **kwargs):
        if info.context.user:
            for group in groups_run_by_user(info.context.user):
                if group_admins(group).count() == 1:
                    raise GraphQLError(json.dumps({"user": [
                        "You are the only admin of " + group.name
                    ]}))
            for collection in collections_owned_by_user(info.context.user):
                if collection_owners(collection).count() == 1:
                    raise GraphQLError(json.dumps({"user": [
                        "You are the only owner of collection: " + collection.name
                    ]}))
            '''for execution in executions_owned_by_user(info.context.user):
                if execution_owners(execution).count() == 1:
                    raise GraphQLError(json.dumps({"user": [
                        "You are the only owner of execution: " + execution.name
                    ]}))'''
            info.context.user.delete()
            return DeleteUserMutation(success=True)
        raise GraphQLError(json.dumps({"username": ["Invalid or missing token"]}))



class LeaveGroupMutation(graphene.Mutation):

    class Arguments:
        id = graphene.ID(required=True)

    group = graphene.Field("core.queries.GroupType")
    user = graphene.Field("core.queries.UserType")

    def mutate(self, info, **kwargs):
        from .permissions import groups_run_by_user, group_admins
        if not info.context.user: raise GraphQLError(json.dumps({"error": ["Not authorized"]}))
        group = Group.objects.filter(id=kwargs["id"]).first()
        if not group: raise GraphQLError('{"group": ["Does not exist"]}')
        link = UserGroupLink.objects.filter(user=info.context.user, group=group, permission__gte=2).first()
        if not link: raise GraphQLError('{"group": ["Not in group"]}')
        if link.permission == 3 and group_admins(group).count() == 1:
            raise GraphQLError('{"group": ["If you left there would be no admins"]}') 
        link.delete()
        return LeaveGroupMutation(group=group, user=info.context.user)



class ProcessGroupInvitationMutation(graphene.Mutation):

    class Arguments:
        user = graphene.ID(required=True)
        group = graphene.ID(required=True)
        accept = graphene.Boolean(required=True)

    success = graphene.Boolean()
    user = graphene.Field("core.queries.UserType")

    def mutate(self, info, **kwargs):
        if not info.context.user:
            raise GraphQLError(json.dumps({"error": "Not authorized"}))
        group = Group.objects.filter(id=kwargs["group"]).first()
        if not group: raise GraphQLError('{"group": ["Does not exist"]}')
        user = User.objects.filter(id=kwargs["user"]).first()
        if not user: raise GraphQLError('{"user": ["Does not exist"]}')
        if user != info.context.user:
            if not group_admins(group).filter(id=info.context.user.id):
                raise GraphQLError('{"user": ["Not for you"]}')
            if kwargs["accept"]: raise GraphQLError('{"user": ["User must accept"]}')
        link = UserGroupLink.objects.filter(user=user, group=group, permission=1).first()
        if not link: raise GraphQLError('{"user": ["No invitation"]}')
        if kwargs["accept"]:
            link.permission = 2
            link.save()
        else:
            link.delete()
        return ProcessGroupInvitationMutation(success=True, user=info.context.user)



class CreateGroupMutation(graphene.Mutation):

    Arguments = create_mutation_arguments(GroupForm)
    
    group = graphene.Field("core.queries.GroupType")
    user = graphene.Field("core.queries.UserType")

    def mutate(self, info, **kwargs):
        if not info.context.user:
            raise GraphQLError(json.dumps({"error": "Not authorized"}))
        form = GroupForm(kwargs)
        if form.is_valid():
            form.save()
            UserGroupLink.objects.create(group=form.instance, user=info.context.user, permission=3)
            return CreateGroupMutation(group=form.instance, user=info.context.user)
        raise GraphQLError(json.dumps(form.errors))



class UpdateGroupMutation(graphene.Mutation):

    Arguments = create_mutation_arguments(GroupForm, edit=True)
    
    group = graphene.Field("core.queries.GroupType")
    user = graphene.Field("core.queries.UserType")

    def mutate(self, info, **kwargs):
        if not info.context.user:
            raise GraphQLError(json.dumps({"error": "Not authorized"}))
        group = Group.objects.filter(id=kwargs["id"])
        if not group: raise GraphQLError('{"group": ["Does not exist"]}')
        if not groups_run_by_user(info.context.user).filter(id=kwargs["id"]):
            raise GraphQLError('{"group": ["Not an admin"]}')
        form = GroupForm(kwargs, instance=group.first())
        if form.is_valid():
            form.save()
            return UpdateGroupMutation(group=form.instance, user=info.context.user)
        raise GraphQLError(json.dumps(form.errors))



class DeleteGroupMutation(graphene.Mutation):

    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    user = graphene.Field("core.queries.UserType")

    def mutate(self, info, **kwargs):
        if not info.context.user:
            raise GraphQLError(json.dumps({"error": "Not authorized"}))
        group = Group.objects.filter(id=kwargs["id"])
        if not group: raise GraphQLError('{"group": ["Does not exist"]}')
        if not groups_run_by_user(info.context.user).filter(id=kwargs["id"]):
            raise GraphQLError('{"group": ["Not an admin"]}')
        group.first().delete()
        return DeleteGroupMutation(success=True, user=info.context.user)



class RevokeGroupAdminMutation(graphene.Mutation):

    class Arguments:
        user = graphene.ID(required=True)
        group = graphene.ID(required=True)

    group = graphene.Field("core.queries.GroupType")
    user = graphene.Field("core.queries.UserType")

    def mutate(self, info, **kwargs):
        if not info.context.user:
            raise GraphQLError(json.dumps({"error": "Not authorized"}))
        group = Group.objects.filter(id=kwargs["group"]).first()
        if not group: raise GraphQLError('{"group": ["Does not exist"]}')
        if not groups_run_by_user(info.context.user).filter(id=kwargs["group"]):
            raise GraphQLError('{"group": ["Not an admin"]}')
        user = User.objects.filter(id=kwargs["user"]).first()
        if not user: raise GraphQLError('{"user": ["Does not exist"]}')
        if not groups_run_by_user(user).filter(id=kwargs["group"]):
            raise GraphQLError('{"group": ["Not an admin"]}')
        if group_admins(group).count() == 1:
            raise GraphQLError('{"user": ["You can\'t resign if you are the only admin"]}')
        link = UserGroupLink.objects.filter(user=user, group=group).first()
        if link.permission != 3: raise GraphQLError('{"user": ["Not an admin"]}')
        link.permission = 2
        link.save()
        return RevokeGroupAdminMutation(group=group, user=user)



class RemoveUserFromGroupMutation(graphene.Mutation):

    class Arguments:
        user = graphene.ID(required=True)
        group = graphene.ID(required=True)

    group = graphene.Field("core.queries.GroupType")

    def mutate(self, info, **kwargs):
        if not info.context.user:
            raise GraphQLError(json.dumps({"error": "Not authorized"}))
        group = Group.objects.filter(id=kwargs["group"]).first()
        if not group: raise GraphQLError('{"group": ["Does not exist"]}')
        if not groups_run_by_user(info.context.user).filter(id=kwargs["group"]):
            raise GraphQLError('{"group": ["Not an admin"]}')
        user = User.objects.filter(id=kwargs["user"]).first()
        if not user: raise GraphQLError('{"user": ["Does not exist"]}')

        link = UserGroupLink.objects.filter(user=user, group=group, permission__gte=2).first()
        if not link:
            raise GraphQLError('{"user": ["Not in group"]}')
        link.delete()
        return RemoveUserFromGroupMutation(group=group)



class InviteUserToGroupMutation(graphene.Mutation):

    class Arguments:
        user = graphene.ID(required=True)
        group = graphene.ID(required=True)

    user = graphene.Field("core.queries.UserType")
    group = graphene.Field("core.queries.GroupType")

    def mutate(self, info, **kwargs):
        if not info.context.user:
            raise GraphQLError(json.dumps({"error": "Not authorized"}))
        group = Group.objects.filter(id=kwargs["group"]).first()
        if not group: raise GraphQLError('{"group": ["Does not exist"]}')
        if not groups_run_by_user(info.context.user).filter(id=kwargs["group"]):
            raise GraphQLError('{"group": ["Not an admin"]}')
        user = User.objects.filter(id=kwargs["user"]).first()
        if not user: raise GraphQLError('{"user": ["Does not exist"]}')
        link = UserGroupLink.objects.filter(user=user, group=group).first()
        if link: raise GraphQLError('{"user": ["Already connected"]}')
        UserGroupLink.objects.create(user=user, group=group, permission=1)
        return InviteUserToGroupMutation(user=user, group=group)



class MakeGroupAdminMutation(graphene.Mutation):

    class Arguments:
        user = graphene.ID(required=True)
        group = graphene.ID(required=True)

    group = graphene.Field("core.queries.GroupType")
    user = graphene.Field("core.queries.UserType")

    def mutate(self, info, **kwargs):
        if not info.context.user:
            raise GraphQLError(json.dumps({"error": "Not authorized"}))
        group = Group.objects.filter(id=kwargs["group"]).first()
        if not group: raise GraphQLError('{"group": ["Does not exist"]}')
        if not groups_run_by_user(info.context.user).filter(id=kwargs["group"]):
            raise GraphQLError('{"group": ["Not an admin"]}')
        user = User.objects.filter(id=kwargs["user"]).first()
        if not user: raise GraphQLError('{"user": ["Does not exist"]}')
        link = UserGroupLink.objects.filter(user=user, group=group).first()
        if not link or link.permission == 1:
            raise GraphQLError('{"user": ["Not a member"]}')
        if link.permission == 3:
            raise GraphQLError('{"user": ["Already an admin"]}')
        link.permission = 3
        link.save()
        return MakeGroupAdminMutation(group=group, user=user)