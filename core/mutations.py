import time
import json
import secrets
import graphene
from graphql import GraphQLError
from django.contrib.auth.hashers import check_password
from django.contrib.auth.password_validation import validate_password
from core.models import User
from core.forms import *
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
                "HTTP_ORIGIN", "https://imaps.goodwright.org"
            ))
            info.context.refresh_token = form.instance.make_refresh_jwt()
            info.context.user = form.instance
            return SignupMutation(
                access_token=form.instance.make_access_jwt(),
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
        user = User.objects.filter(username=kwargs["username"]).first()
        if user:
            if check_password(kwargs["password"], user.password):
                info.context.refresh_token = user.make_refresh_jwt()
                info.context.user = user
                user.last_login = time.time()
                user.save()
                return LoginMutation(access_token=user.make_access_jwt(), user=user)
        raise GraphQLError(json.dumps({"username": "Invalid credentials"}))



class LogoutMutation(graphene.Mutation):
    
    success = graphene.Boolean()

    def mutate(self, info, **kwargs):
        info.context.refresh_token = False
        return LogoutMutation(success=True)



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



class RequestPasswordResetMutation(graphene.Mutation):

    class Arguments:
        email = graphene.String()

    success = graphene.Boolean()

    def mutate(self, info, **kwargs):
        matches = User.objects.filter(email=kwargs["email"])
        random_token = secrets.token_hex(64)
        reset_url = info.context.META.get(
            "HTTP_ORIGIN", "https://imaps.goodwright.org"
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
                raise GraphQLError(json.dumps({"password": [str(e.error_list[0])]}))
            user.set_password(kwargs["password"])
            user.password_reset_token = ""
            user.password_reset_token_expiry = 0
            user.save()
            return ResetPasswordMutation(success=True)
        raise GraphQLError(json.dumps({"token": ["Token is not valid"]}))



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
        user = info.context.user
        if user:
            for group in user.admin_groups.all():
                if group.admins.count() == 1:
                    raise GraphQLError(json.dumps({"user": ["You are the only admin of " + group.name]}))
            for collection in user.collections.filter(collectionuserlink__is_owner=True):
                if collection.users.filter(collectionuserlink__is_owner=True).count() == 1:
                    raise GraphQLError(json.dumps({"user": ["You are the only owner of collection: " + collection.name]}))
            user.delete()
            return DeleteUserMutation(success=True)
        raise GraphQLError(json.dumps({"username": ["Invalid or missing token"]}))



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
            form.instance.users.add(info.context.user)
            form.instance.admins.add(info.context.user)
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
        if not info.context.user.admin_groups.filter(id=kwargs["id"]):
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
        if not info.context.user.admin_groups.filter(id=kwargs["id"]):
            raise GraphQLError('{"group": ["Not an admin"]}')
        group.first().delete()
        return DeleteGroupMutation(success=True, user=info.context.user)



class InviteUserToGroup(graphene.Mutation):

    class Arguments:
        user = graphene.ID(required=True)
        group = graphene.ID(required=True)

    invitation = graphene.Field("core.queries.GroupInvitationType")

    def mutate(self, info, **kwargs):
        if not info.context.user:
            raise GraphQLError(json.dumps({"error": "Not authorized"}))
        group = Group.objects.filter(id=kwargs["group"])
        if not group: raise GraphQLError('{"group": ["Does not exist"]}')
        if not info.context.user.admin_groups.filter(id=kwargs["group"]):
            raise GraphQLError('{"group": ["Not an admin"]}')
        user = User.objects.filter(id=kwargs["user"])
        if not user: raise GraphQLError('{"user": ["Does not exist"]}')
        if user.first().groups.filter(id=kwargs["group"]):
            raise GraphQLError('{"user": ["Already a member"]}')
        if user.first().group_invitations.filter(group=kwargs["group"]):
            raise GraphQLError('{"user": ["Already invited"]}')
        invitation = GroupInvitation.objects.create(
            user=user.first(), group=group.first()
        )
        return InviteUserToGroup(invitation=invitation)



class DeleteGroupInvitationMutation(graphene.Mutation):

    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    user = graphene.Field("core.queries.UserType")

    def mutate(self, info, **kwargs):
        if not info.context.user:
            raise GraphQLError(json.dumps({"error": "Not authorized"}))
        invitation = GroupInvitation.objects.filter(id=kwargs["id"])
        if not invitation: raise GraphQLError('{"invitation": ["Does not exist"]}')
        if invitation.first().user != info.context.user:
            if not invitation.first().group.admins.filter(id=info.context.user.id):
                raise GraphQLError('{"invitation": ["Does not exist"]}')
        invitation.first().delete()
        return DeleteGroupInvitationMutation(success=True, user=info.context.user)



class AcceptGroupInvitationMutation(graphene.Mutation):

    class Arguments:
        id = graphene.ID(required=True)

    group = graphene.Field("core.queries.GroupType")
    user = graphene.Field("core.queries.UserType")

    def mutate(self, info, **kwargs):
        if not info.context.user:
            raise GraphQLError(json.dumps({"error": "Not authorized"}))
        invitation = GroupInvitation.objects.filter(id=kwargs["id"])
        if not invitation: raise GraphQLError('{"invitation": ["Does not exist"]}')
        if invitation.first().user != info.context.user:
            raise GraphQLError('{"invitation": ["Does not exist"]}')
        group = invitation.first().group
        invitation.first().delete()
        group.users.add(info.context.user)
        return AcceptGroupInvitationMutation(group=group, user=info.context.user)



class MakeGroupAdminMutation(graphene.Mutation):

    class Arguments:
        user = graphene.ID(required=True)
        group = graphene.ID(required=True)

    group = graphene.Field("core.queries.GroupType")
    user = graphene.Field("core.queries.UserType")

    def mutate(self, info, **kwargs):
        if not info.context.user:
            raise GraphQLError(json.dumps({"error": "Not authorized"}))
        group = Group.objects.filter(id=kwargs["group"])
        if not group: raise GraphQLError('{"group": ["Does not exist"]}')
        if not info.context.user.admin_groups.filter(id=kwargs["group"]):
            raise GraphQLError('{"group": ["Not an admin"]}')
        user = User.objects.filter(id=kwargs["user"])
        if not user: raise GraphQLError('{"user": ["Does not exist"]}')
        if group.first().users.filter(id=user.first().id).count() == 0:
            raise GraphQLError('{"user": ["Not a member"]}')
        if group.first().admins.filter(id=user.first().id).count():
            raise GraphQLError('{"user": ["Already an admin"]}')
        group.first().admins.add(user.first())
        return MakeGroupAdminMutation(group=group.first(), user=user.first())



class RevokeGroupAdminMutation(graphene.Mutation):

    class Arguments:
        user = graphene.ID(required=True)
        group = graphene.ID(required=True)

    group = graphene.Field("core.queries.GroupType")
    user = graphene.Field("core.queries.UserType")

    def mutate(self, info, **kwargs):
        if not info.context.user:
            raise GraphQLError(json.dumps({"error": "Not authorized"}))
        group = Group.objects.filter(id=kwargs["group"])
        if not group: raise GraphQLError('{"group": ["Does not exist"]}')
        if not info.context.user.admin_groups.filter(id=kwargs["group"]):
            raise GraphQLError('{"group": ["Not an admin"]}')
        user = User.objects.filter(id=kwargs["user"])
        if not user: raise GraphQLError('{"user": ["Does not exist"]}')
        if group.first().admins.filter(id=user.first().id).count() == 0:
            raise GraphQLError('{"user": ["Not an admin"]}')
        if group.first().admins.count() == 1:
            raise GraphQLError('{"user": ["You can\'t resign if you are the only admin"]}')
        group.first().admins.remove(user.first())
        return RevokeGroupAdminMutation(group=group.first(), user=user.first())



class RemoveUserFromGroup(graphene.Mutation):

    class Arguments:
        user = graphene.ID(required=True)
        group = graphene.ID(required=True)

    group = graphene.Field("core.queries.GroupType")

    def mutate(self, info, **kwargs):
        if not info.context.user:
            raise GraphQLError(json.dumps({"error": "Not authorized"}))
        group = Group.objects.filter(id=kwargs["group"])
        if not group: raise GraphQLError('{"group": ["Does not exist"]}')
        if not info.context.user.admin_groups.filter(id=kwargs["group"]):
            raise GraphQLError('{"group": ["Not an admin"]}')
        user = User.objects.filter(id=kwargs["user"])
        if not user: raise GraphQLError('{"user": ["Does not exist"]}')
        if group.first().users.filter(id=user.first().id).count() == 0:
            raise GraphQLError('{"user": ["Not in group"]}')
        group.first().users.remove(user.first())
        group.first().admins.remove(user.first())
        return RemoveUserFromGroup(group=group.first())



class LeaveGroup(graphene.Mutation):

    class Arguments:
        id = graphene.ID(required=True)

    group = graphene.Field("core.queries.GroupType")
    user = graphene.Field("core.queries.UserType")

    def mutate(self, info, **kwargs):
        if not info.context.user:
            raise GraphQLError(json.dumps({"error": ["Not authorized"]}))
        group = Group.objects.filter(id=kwargs["id"])
        if not group: raise GraphQLError('{"group": ["Does not exist"]}')
        if group.first().users.filter(id=info.context.user.id).count() == 0:
            raise GraphQLError('{"group": ["Not in group"]}')
        if group.first().admins.count() == 1:
            if group.first().admins.filter(id=info.context.user.id).count():
                raise GraphQLError('{"group": ["If you left there would be no admins"]}')
        group.first().users.remove(info.context.user)
        group.first().admins.remove(info.context.user)
        return LeaveGroup(group=group.first(), user=info.context.user)