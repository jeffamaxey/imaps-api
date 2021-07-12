import time
import json
import os
import secrets
import graphene
import jinja2
import re
from graphql import GraphQLError
from graphene_file_upload.scalars import Upload
from django.contrib.auth.hashers import check_password
from django.contrib.auth.password_validation import validate_password
from core.models import User
from core.forms import *
from core.email import send_welcome_email, send_reset_email, send_reset_warning_email
from core.arguments import create_mutation_arguments
from .celery import run_command

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
            info.context.imaps_refresh_token = form.instance.make_refresh_jwt()
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
        time.sleep(1)
        user = User.objects.filter(username=kwargs["username"]).first()
        if user:
            if check_password(kwargs["password"], user.password):
                info.context.imaps_refresh_token = user.make_refresh_jwt()
                info.context.user = user
                user.last_login = time.time()
                user.save()
                return LoginMutation(access_token=user.make_access_jwt(), user=user)
        raise GraphQLError(json.dumps({"username": "Invalid credentials"}))



class LogoutMutation(graphene.Mutation):
    
    success = graphene.Boolean()

    def mutate(self, info, **kwargs):
        info.context.imaps_refresh_token = False
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
                raise GraphQLError(json.dumps({"password": [str(e.error_list[0])[2:-2]]}))
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
            for collection in user.owned_collections:
                if collection.owners.count() == 1:
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

    user = graphene.Field("core.queries.UserType")
    group = graphene.Field("core.queries.GroupType")

    def mutate(self, info, **kwargs):
        if not info.context.user:
            raise GraphQLError(json.dumps({"error": "Not authorized"}))
        group = Group.objects.filter(id=kwargs["group"]).first()
        if not group: raise GraphQLError('{"group": ["Does not exist"]}')
        if not info.context.user.admin_groups.filter(id=kwargs["group"]):
            raise GraphQLError('{"group": ["Not an admin"]}')
        user = User.objects.filter(id=kwargs["user"]).first()
        if not user: raise GraphQLError('{"user": ["Does not exist"]}')
        link = UserGroupLink.objects.filter(user=user, group=group).first()
        if link: raise GraphQLError('{"user": ["Already connected"]}')
        UserGroupLink.objects.create(user=user, group=group, permission=1)
        return InviteUserToGroup(user=user, group=group)



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
            if not group.admins.filter(id=info.context.user.id):
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
        if not info.context.user.admin_groups.filter(id=kwargs["group"]):
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
        if not info.context.user.admin_groups.filter(id=kwargs["group"]):
            raise GraphQLError('{"group": ["Not an admin"]}')
        user = User.objects.filter(id=kwargs["user"]).first()
        if not user: raise GraphQLError('{"user": ["Does not exist"]}')
        if not user.admin_groups.filter(id=kwargs["group"]):
            raise GraphQLError('{"group": ["Not an admin"]}')
        if group.admins.count() == 1:
            raise GraphQLError('{"user": ["You can\'t resign if you are the only admin"]}')
        link = UserGroupLink.objects.filter(user=user, group=group).first()
        if link.permission != 3: raise GraphQLError('{"user": ["Not an admin"]}')
        link.permission = 2
        link.save()
        return RevokeGroupAdminMutation(group=group, user=user)



class RemoveUserFromGroup(graphene.Mutation):

    class Arguments:
        user = graphene.ID(required=True)
        group = graphene.ID(required=True)

    group = graphene.Field("core.queries.GroupType")

    def mutate(self, info, **kwargs):
        if not info.context.user:
            raise GraphQLError(json.dumps({"error": "Not authorized"}))
        group = Group.objects.filter(id=kwargs["group"]).first()
        if not group: raise GraphQLError('{"group": ["Does not exist"]}')
        if not info.context.user.admin_groups.filter(id=kwargs["group"]):
            raise GraphQLError('{"group": ["Not an admin"]}')
        user = User.objects.filter(id=kwargs["user"]).first()
        if not user: raise GraphQLError('{"user": ["Does not exist"]}')

        link = UserGroupLink.objects.filter(user=user, group=group, permission__gte=2).first()
        if not link:
            raise GraphQLError('{"user": ["Not in group"]}')
        link.delete()
        return RemoveUserFromGroup(group=group)



class LeaveGroup(graphene.Mutation):

    class Arguments:
        id = graphene.ID(required=True)

    group = graphene.Field("core.queries.GroupType")
    user = graphene.Field("core.queries.UserType")

    def mutate(self, info, **kwargs):
        if not info.context.user:
            raise GraphQLError(json.dumps({"error": ["Not authorized"]}))
        group = Group.objects.filter(id=kwargs["id"]).first()
        if not group: raise GraphQLError('{"group": ["Does not exist"]}')
        link = UserGroupLink.objects.filter(user=info.context.user, group=group, permission__gte=2).first()
        if not link: raise GraphQLError('{"group": ["Not in group"]}')
        if link.permission == 3 and group.admins.count() == 1:
            raise GraphQLError('{"group": ["If you left there would be no admins"]}')
        link.delete()
        return LeaveGroup(group=group, user=info.context.user)



class CreateCollectionMutation(graphene.Mutation):

    Arguments = create_mutation_arguments(CollectionForm)
    
    collection = graphene.Field("core.queries.CollectionType")

    def mutate(self, info, **kwargs):
        if not info.context.user:
            raise GraphQLError(json.dumps({"error": "Not authorized"}))
        form = CollectionForm(kwargs)
        if form.is_valid():
            form.save()
            CollectionUserLink.objects.create(collection=form.instance, user=info.context.user, permission=4)
            return CreateCollectionMutation(collection=form.instance)
        raise GraphQLError(json.dumps(form.errors))



class PaperInput(graphene.InputObjectType):
    title = graphene.String(required=True)
    year = graphene.Int(required=True)
    url = graphene.String(required=True)



class UpdateCollectionMutation(graphene.Mutation):

    Arguments = create_mutation_arguments(
        CollectionForm, edit=True, papers=graphene.List(PaperInput)
    )
    
    collection = graphene.Field("core.queries.CollectionType")

    def mutate(self, info, **kwargs):
        if not info.context.user:
            raise GraphQLError(json.dumps({"error": "Not authorized"}))
        collection = Collection.objects.filter(id=kwargs["id"]).viewable_by(info.context.user).first()
        if not collection: raise GraphQLError('{"collection": ["Does not exist"]}')
        if info.context.user not in collection.editors:
            for group in info.context.user.memberships.all():
                if group in collection.group_editors: break
            else:
                raise GraphQLError('{"collection": ["You don\'t have permission to edit this collection"]}')
        form = CollectionForm(kwargs, instance=collection)
        if form.is_valid():
            if "papers" in kwargs:
                collection.papers.all().delete()
                for paper in kwargs["papers"]:
                    paper_form = PaperForm({**paper, "collection": collection.id})
                    if paper_form.is_valid():
                        paper_form.save()
                    else: raise GraphQLError(json.dumps(paper_form.errors))
            form.save()
            return UpdateCollectionMutation(collection=form.instance)
        raise GraphQLError(json.dumps(form.errors))



class UpdateCollectionAccessMutation(graphene.Mutation):

    class Arguments:
        id = graphene.ID(required=True)
        user = graphene.ID()
        group = graphene.ID()
        permission = graphene.Int(required=True)
    
    collection = graphene.Field("core.queries.CollectionType")
    user = graphene.Field("core.queries.UserType")
    group = graphene.Field("core.queries.GroupType")

    def mutate(self, info, **kwargs):
        if not info.context.user: raise GraphQLError(json.dumps({"error": "Not authorized"}))
        collection = Collection.objects.filter(
            id=kwargs["id"]
        ).viewable_by(info.context.user).first()
        if not collection: raise GraphQLError('{"collection": ["Does not exist"]}')
        if info.context.user not in collection.sharers and all(
            group not in collection.group_sharers for group in info.context.user.memberships
        ):
            raise GraphQLError('{"collection": ["You do not have share permissions"]}')
        user = User.objects.filter(id=kwargs.get("user")).first()
        if kwargs.get("user") and not user: raise GraphQLError('{"user": ["Does not exist"]}')
        group = Group.objects.filter(id=kwargs.get("group")).first()
        if kwargs.get("group") and not group: raise GraphQLError('{"group": ["Does not exist"]}')
        if user:
            if not 0 <= kwargs["permission"] <= 4:
                raise GraphQLError('{"permission": ["Not a valid permission"]}')
            link = CollectionUserLink.objects.get_or_create(
                collection=collection, user=user
            )[0]
            if kwargs["permission"] == 4 and info.context.user not in collection.owners:
                raise GraphQLError('{"collection": ["Only an owner can make owners"]}')
            if link.permission == 4 and info.context.user not in collection.owners:
                raise GraphQLError('{"collection": ["Only an owner can remove owners"]}')
            if collection.owners.count() == 1 and link.permission == 4 and kwargs["permission"] != 4:
                raise GraphQLError('{"collection": ["There must be at least one owner"]}')
        elif group:
            if not 0 <= kwargs["permission"] <= 3:
                raise GraphQLError('{"permission": ["Not a valid permission"]}')
            link = CollectionGroupLink.objects.get_or_create(
                collection=collection, group=group
            )[0]
        else:
            raise GraphQLError('{"user": ["Must provide user or group"]}')
        if kwargs["permission"] == 0:
            link.delete()
        else:
            link.permission = kwargs["permission"]
            link.save()
        return UpdateCollectionAccessMutation(user=user, collection=collection, group=group)



class DeleteCollectionMutation(graphene.Mutation):

    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()

    def mutate(self, info, **kwargs):
        if not info.context.user:
            raise GraphQLError(json.dumps({"error": "Not authorized"}))
        collection = Collection.objects.filter(id=kwargs["id"]).viewable_by(info.context.user).first()
        if not collection: raise GraphQLError('{"collection": ["Does not exist"]}')
        if info.context.user not in collection.owners:
            raise GraphQLError('{"collection": ["Not an owner"]}')
        executions = (
            Execution.objects.filter(collection=collection) |
            Execution.objects.filter(sample__collection=collection)
        )
        executions.delete()
        collection.delete()
        return DeleteCollectionMutation(success=True)



class UpdateSampleMutation(graphene.Mutation):

    Arguments = create_mutation_arguments(
        SampleForm, edit=True, collection=graphene.ID(required=True)
    )
    
    sample = graphene.Field("core.queries.SampleType")

    def mutate(self, info, **kwargs):
        if not info.context.user:
            raise GraphQLError(json.dumps({"error": "Not authorized"}))
        sample = Sample.objects.filter(id=kwargs["id"]).viewable_by(info.context.user).first()
        if not sample: raise GraphQLError('{"sample": ["Does not exist"]}')
        collection = Collection.objects.filter(id=kwargs["collection"]).viewable_by(info.context.user).first()
        if not collection: raise GraphQLError('{"collection": ["Does not exist"]}')
        if collection not in info.context.user.owned_collections:
            raise GraphQLError('{"collection": ["Collection not owned"]}')
        if info.context.user not in sample.editors:
            if not sample.collection or info.context.user not in sample.collection.editors:
                raise GraphQLError('{"sample": ["You don\'t have permission to edit this sample"]}')
        form = SampleForm(kwargs, instance=sample)
        if form.is_valid():
            form.save()
            return UpdateSampleMutation(sample=form.instance)
        raise GraphQLError(json.dumps(form.errors))



class UpdateSampleAccessMutation(graphene.Mutation):

    class Arguments:
        id = graphene.ID(required=True)
        user = graphene.ID()
        permission = graphene.Int(required=True)
    
    sample = graphene.Field("core.queries.SampleType")
    user = graphene.Field("core.queries.UserType")

    def mutate(self, info, **kwargs):
        if not info.context.user: raise GraphQLError(json.dumps({"error": "Not authorized"}))
        sample = Sample.objects.filter(
            id=kwargs["id"]
        ).viewable_by(info.context.user).first()
        if not sample: raise GraphQLError('{"sample": ["Does not exist"]}')
        if info.context.user not in sample.sharers and all(
            group not in sample.collection.group_sharers for group in info.context.user.memberships
        ) and (not sample.collection or info.context.user not in sample.collection.sharers):
            raise GraphQLError('{"sample": ["You do not have share permissions"]}')
        user = User.objects.filter(id=kwargs.get("user")).first()
        if kwargs.get("user") and not user: raise GraphQLError('{"user": ["Does not exist"]}')
        if not 0 <= kwargs["permission"] <= 3:
            raise GraphQLError('{"permission": ["Not a valid permission"]}')
        link = SampleUserLink.objects.get_or_create(
            sample=sample, user=user
        )[0]
        if kwargs["permission"] == 0:
            link.delete()
        else:
            link.permission = kwargs["permission"]
            link.save()
        return UpdateSampleAccessMutation(user=user, sample=sample)



class DeleteSampleMutation(graphene.Mutation):

    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()

    def mutate(self, info, **kwargs):
        if not info.context.user:
            raise GraphQLError(json.dumps({"error": "Not authorized"}))
        sample = Sample.objects.filter(id=kwargs["id"]).viewable_by(info.context.user).first()
        if not sample: raise GraphQLError('{"sample": ["Does not exist"]}')
        if info.context.user not in sample.collection.owners:
            raise GraphQLError('{"sample": ["Not an owner"]}')
        executions = Execution.objects.filter(sample=sample)
        executions.delete()
        sample.delete()
        return DeleteSampleMutation(success=True)



class UpdateExecutionMutation(graphene.Mutation):

    Arguments = create_mutation_arguments(ExecutionForm, edit=True)
    
    execution = graphene.Field("core.queries.ExecutionType")

    def mutate(self, info, **kwargs):
        if not info.context.user:
            raise GraphQLError(json.dumps({"error": "Not authorized"}))
        execution = Execution.objects.filter(id=kwargs["id"]).viewable_by(info.context.user).first()
        if not execution: raise GraphQLError('{"execution": ["Does not exist"]}')
        if info.context.user not in execution.editors:
            raise GraphQLError('{"execution": ["You don\'t have permission to edit this execution"]}')
        form = ExecutionForm(kwargs, instance=execution)
        if form.is_valid():
            form.save()
            return UpdateExecutionMutation(execution=form.instance)
        raise GraphQLError(json.dumps(form.errors))



class UpdateExecutionAccessMutation(graphene.Mutation):

    class Arguments:
        id = graphene.ID(required=True)
        user = graphene.ID()
        permission = graphene.Int(required=True)
    
    execution = graphene.Field("core.queries.ExecutionType")
    user = graphene.Field("core.queries.UserType")

    def mutate(self, info, **kwargs):
        if not info.context.user: raise GraphQLError(json.dumps({"error": "Not authorized"}))
        execution = Execution.objects.filter(
            id=kwargs["id"]
        ).viewable_by(info.context.user).first()
        if not execution: raise GraphQLError('{"execution": ["Does not exist"]}')
        if info.context.user not in execution.sharers and all(
            group not in execution.collection.group_sharers for group in info.context.user.memberships
        ):
            raise GraphQLError('{"execution": ["You do not have share permissions"]}')
        user = User.objects.filter(id=kwargs.get("user")).first()
        if kwargs.get("user") and not user: raise GraphQLError('{"user": ["Does not exist"]}')
        if not 0 <= kwargs["permission"] <= 4:
            raise GraphQLError('{"permission": ["Not a valid permission"]}')
        link = ExecutionUserLink.objects.get_or_create(
            execution=execution, user=user
        )[0]
        if kwargs["permission"] == 4 and info.context.user not in execution.owners:
            raise GraphQLError('{"execution": ["Only an owner can make owners"]}')
        if link.permission == 4 and info.context.user not in execution.owners:
            raise GraphQLError('{"execution": ["Only an owner can remove owners"]}')
        
        if kwargs["permission"] == 0:
            link.delete()
        else:
            link.permission = kwargs["permission"]
            link.save()
        return UpdateExecutionAccessMutation(user=user, execution=execution)



class DeleteExecutionMutation(graphene.Mutation):

    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()

    def mutate(self, info, **kwargs):
        if not info.context.user:
            raise GraphQLError(json.dumps({"error": "Not authorized"}))
        execution = Execution.objects.filter(id=kwargs["id"]).viewable_by(info.context.user).first()
        if not execution: raise GraphQLError('{"execution": ["Does not exist"]}')
        if info.context.user not in execution.owners:
            raise GraphQLError('{"execution": ["Not an owner"]}')
        execution.delete()
        return DeleteExecutionMutation(success=True)


def sample_name(id):
    sample = Execution.objects.get(id=id).sample
    return sample.name if sample else None
def name(id):
    name_ = Execution.objects.get(id=id).name
    match = re.match(r".+ \((.+?)\)", name_)
    if match: name_ = match[1]
    return name_
jinja2.filters.FILTERS["sample_name"] = sample_name
jinja2.filters.FILTERS["name"] = name

class RunCommandMutation(graphene.Mutation):

    class Arguments:
        command = graphene.ID(required=True)
        collection = graphene.ID()
        inputs = graphene.String(required=True)
        uploads = graphene.List(Upload)

    execution = graphene.Field("core.queries.ExecutionType")

    def mutate(self, info, **kwargs):
        if not info.context.user:
            raise GraphQLError(json.dumps({"error": "Not authorized"}))
        command = Command.objects.get(id=kwargs["command"])
        template = jinja2.Template(command.data_name)
        schema = json.loads(command.input_schema)
        inputs = json.loads(kwargs["inputs"])
        executions = []
        for input in schema:
            if "list:data:" in input.get("type"):
                executions += [Execution.objects.get(id=id) for id in inputs[input["name"]]]
            elif "data:" in input.get("type"):
                executions.append(Execution.objects.get(id=inputs[input["name"]]))
        samples = set([e.sample_id for e in executions if e.sample_id])
        execution = Execution.objects.create(
            name=template.render(**inputs),
            command=command,
            status="Running",
            sample_id=list(samples)[0] if len(samples) == 1 else None,
            collection_id=kwargs.get("collection"),
            input=kwargs["inputs"],
            user=info.context.user,
        )
        ExecutionUserLink.objects.create(execution=execution, user=info.context.user, permission=4)
        os.mkdir(os.path.join(settings.DATA_ROOT, str(execution.id)))
        for upload in kwargs.get("uploads", []):
            with open(os.path.join(settings.DATA_ROOT, str(execution.id), upload.name), "wb+") as f:
                for chunk in upload.chunks():
                    f.write(chunk)
        run = json.loads(command.run)
        extension = "py" if run.get("language") == "python" else "sh"
        with open(os.path.join(settings.DATA_ROOT, str(execution.id), f"run.{extension}"), "w") as f:
            template = jinja2.Template(run["program"])
            f.write(template.render(**inputs))
        run_command.apply_async((execution.id, inputs, json.loads(command.requirements)))
        return RunCommandMutation(execution=execution)