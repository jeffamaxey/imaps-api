import json
import graphene
from graphene_django.types import DjangoObjectType
from graphene.relay import Connection, ConnectionField
from .models import *

class UserType(DjangoObjectType):
    
    class Meta:
        model = User
        exclude_fields = ["password"]
    
    id = graphene.ID()
    groups = graphene.List("core.queries.GroupType")
    admin_groups = graphene.List("core.queries.GroupType")
    group_invitations = graphene.List("core.queries.GroupInvitationType")
    collections = graphene.List("core.queries.CollectionType")

    def resolve_email(self, info, **kwargs):
        if self != info.context.user: return ""
        return self.email


    def resolve_last_login(self, info, **kwargs):
        if self != info.context.user: return None
        return self.last_login
        

    def resolve_groups(self, info, **kwargs):
        admin_groups = list(self.admin_groups.all())
        return sorted(self.groups.all(), key = lambda g: g not in admin_groups)
    

    def resolve_admin_groups(self, info, **kwargs):
        if self != info.context.user: return None
        return self.admin_groups.all()
    

    def resolve_group_invitations(self, info, **kwargs):
        if self != info.context.user: return None
        return self.group_invitations.all()
    

    def resolve_collections(self, info, **kwargs):
        return self.collections.filter(private=False, collectionuserlink__is_owner=True)



class GroupType(DjangoObjectType):
    
    class Meta:
        model = Group
    
    id = graphene.ID()
    user_count = graphene.Int()
    users = graphene.List("core.queries.UserType")
    admins = graphene.List("core.queries.UserType")
    group_invitations = graphene.List("core.queries.GroupInvitationType")
    collections = graphene.List("core.queries.CollectionType")

    def resolve_user_count(self, info, **kwargs):
        return self.users.count()
        

    def resolve_users(self, info, **kwargs):
        return self.users.all()
    

    def resolve_admins(self, info, **kwargs):
        return self.admins.all()
    

    def resolve_group_invitations(self, info, **kwargs):
        if info.context.user and self.admins.filter(username=info.context.user.username):
            return self.group_invitations.all()
        return None
    

    def resolve_collections(self, info, **kwargs):
        return self.collections.filter(private=False)



class GroupInvitationType(DjangoObjectType):
    
    class Meta:
        model = GroupInvitation
    
    id = graphene.ID()



class CollectionType(DjangoObjectType):
    
    class Meta:
        model = Collection
    
    id = graphene.ID()
    owners = graphene.List("core.queries.UserType")
    papers = graphene.List("core.queries.PaperType")
    samples = graphene.List("core.queries.SampleType")
    executions = graphene.List("core.queries.ExecutionType")
    sample_count = graphene.Int()
    execution_count = graphene.Int()

    def resolve_papers(self, info, **kwargs):
        return self.papers.all()
    
    
    def resolve_owners(self, info, **kwargs):
        return self.users.filter(collectionuserlink__is_owner=True)


    def resolve_samples(self, info, **kwargs):
        return self.samples.all().viewable_by(info.context.user)


    def resolve_executions(self, info, **kwargs):
        return self.executions.all().viewable_by(info.context.user)
    

    def resolve_sample_count(self, info, **kwargs):
        return self.samples.count()


    def resolve_execution_count(self, info, **kwargs):
        return self.executions.count()



class CollectionConnection(Connection):

    class Meta:
        node = CollectionType
    
    count = graphene.Int()

    def resolve_count(self, info, **kwargs):
        print(self.iterable)
        return len(self.iterable)



class PaperType(DjangoObjectType):
    
    class Meta:
        model = Paper
    
    id = graphene.ID()



class SampleType(DjangoObjectType):
    
    class Meta:
        model = Sample
    
    id = graphene.ID()
    executions = graphene.List("core.queries.ExecutionType")


    def resolve_executions(self, info, **kwargs):
        return self.executions.all().viewable_by(info.context.user)



class SampleConnection(Connection):

    class Meta:
        node = SampleType
    
    count = graphene.Int()

    def resolve_count(self, info, **kwargs):
        return len(self.iterable)



class CommandType(DjangoObjectType):
    
    class Meta:
        model = Command
    
    id = graphene.ID()



class ExecutionType(DjangoObjectType):
    
    class Meta:
        model = Execution
    
    id = graphene.ID()
    command = graphene.Field("core.queries.CommandType")
    owners = graphene.List("core.queries.UserType")
    parent = graphene.Field("core.queries.ExecutionType")
    upstream_executions = graphene.List("core.queries.ExecutionType")
    downstream_executions = graphene.List("core.queries.ExecutionType")
    component_executions = graphene.List("core.queries.ExecutionType")

    def resolve_owners(self, info, **kwargs):
        return self.users.filter(executionuserlink__is_owner=True)


    def resolve_upstream_executions(self, info, **kwargs):
        return self.upstream.viewable_by(info.context.user)
    

    def resolve_downstream_executions(self, info, **kwargs):
        return self.downstream.viewable_by(info.context.user)
    

    def resolve_component_executions(self, info, **kwargs):
        return self.components.viewable_by(info.context.user)



class ExecutionConnection(Connection):

    class Meta:
        node = ExecutionType
    
    count = graphene.Int()

    def resolve_count(self, info, **kwargs):
        return len(self.iterable)



class SearchType(graphene.ObjectType):

    results = graphene.List("core.queries.ResultType")



class ResultType(graphene.ObjectType):

    name = graphene.String()
    pk = graphene.ID()
    kind = graphene.String()
    match = graphene.String()
    match_loc = graphene.List(graphene.Int)