import os
import graphene
import json
from graphene_django.types import DjangoObjectType
from graphene.relay import Connection
from .models import *

class UserType(DjangoObjectType):
    
    class Meta:
        model = User
        exclude_fields = ["password"]
    
    id = graphene.ID()

    groups = graphene.List("core.queries.GroupType")
    admin_groups = graphene.List("core.queries.GroupType")
    memberships = graphene.List("core.queries.GroupType")
    invitations = graphene.List("core.queries.GroupType")

    collections = graphene.List("core.queries.CollectionType")
    collection_permission = graphene.Int(id=graphene.ID(required=True))
    owned_collections = graphene.List("core.queries.CollectionType")
    shareable_collections = graphene.List("core.queries.CollectionType")
    editable_collections = graphene.List("core.queries.CollectionType")
    public_collections = graphene.List("core.queries.CollectionType")

    samples = graphene.List("core.queries.SampleType")
    sample_permission = graphene.Int(id=graphene.ID(required=True))
    shareable_samples = graphene.List("core.queries.SampleType")
    editable_samples = graphene.List("core.queries.SampleType")
    public_samples = graphene.List("core.queries.SampleType")

    executions = graphene.List("core.queries.ExecutionType")
    uploads = graphene.List("core.queries.ExecutionType")
    execution_permission = graphene.Int(id=graphene.ID(required=True))
    owned_executions = graphene.List("core.queries.ExecutionType")
    shareable_executions = graphene.List("core.queries.ExecutionType")
    public_executions = graphene.List("core.queries.ExecutionType")

    def resolve_email(self, info, **kwargs):
        if self != info.context.user: return ""
        return self.email


    def resolve_last_login(self, info, **kwargs):
        if self != info.context.user: return None
        return self.last_login
    

    def resolve_groups(self, info, **kwargs):
        return self.groups.all()
        

    def resolve_collections(self, info, **kwargs):
        return self.collections.all().viewable_by(info.context.user)
    

    def resolve_collection_permission(self, info, **kwargs):
        collection = Collection.objects.filter(
            id=kwargs["id"]
        ).viewable_by(info.context.user).first()
        link = CollectionUserLink.objects.filter(user=self, collection=collection).first()
        return link.permission if link else 0
        

    def resolve_owned_collections(self, info, **kwargs):
        return self.owned_collections.viewable_by(info.context.user)
        

    def resolve_shareable_collections(self, info, **kwargs):
        return self.shareable_collections.viewable_by(info.context.user)
        

    def resolve_editable_collections(self, info, **kwargs):
        return self.editable_collections.viewable_by(info.context.user)
    

    def resolve_public_collections(self, info, **kwargs):
        return self.owned_collections.filter(private=False)
    

    def resolve_samples(self, info, **kwargs):
        return self.samples.all().viewable_by(info.context.user)
    

    def resolve_sample_permission(self, info, **kwargs):
        sample = Sample.objects.filter(
            id=kwargs["id"]
        ).viewable_by(info.context.user).first()
        link = SampleUserLink.objects.filter(user=self, sample=sample).first()
        return link.permission if link else 0
        

    def resolve_shareable_samples(self, info, **kwargs):
        return self.shareable_samples.viewable_by(info.context.user)
        

    def resolve_editable_samples(self, info, **kwargs):
        return self.editable_samples.viewable_by(info.context.user)
    

    def resolve_public_samples(self, info, **kwargs):
        return self.samples.filter(private=False)
    

    def resolve_executions(self, info, **kwargs):
        return self.executions.all().viewable_by(info.context.user)

    
    def resolve_uploads(self, info, **kwargs):
        return self.owned_executions.filter(
            command__category="import"
        ).viewable_by(info.context.user).order_by("-created")
    

    def resolve_execution_permission(self, info, **kwargs):
        execution = Execution.objects.filter(
            id=kwargs["id"]
        ).viewable_by(info.context.user).first()
        link = ExecutionUserLink.objects.filter(user=self, execution=execution).first()
        return link.permission if link else 0
        

    def resolve_owned_executions(self, info, **kwargs):
        return self.owned_executions.viewable_by(info.context.user)
        

    def resolve_shareable_executions(self, info, **kwargs):
        return self.shareable_executions.viewable_by(info.context.user)
        

    def resolve_editable_executions(self, info, **kwargs):
        return self.editable_executions.viewable_by(info.context.user)
    

    def resolve_public_executions(self, info, **kwargs):
        return self.executions.filter(private=False)



class GroupType(DjangoObjectType):
    
    class Meta:
        model = Group
    
    id = graphene.ID()
    user_count = graphene.Int()
    users = graphene.List("core.queries.UserType")
    admins = graphene.List("core.queries.UserType")
    members = graphene.List("core.queries.UserType")
    invitees = graphene.List("core.queries.UserType")
    collections = graphene.List("core.queries.CollectionType")
    collection_permission = graphene.Int(id=graphene.ID(required=True))
    shareable_collections = graphene.List("core.queries.CollectionType")
    editable_collections = graphene.List("core.queries.CollectionType")
    public_collections = graphene.List("core.queries.CollectionType")

    def resolve_users(self, info, **kwargs):
        return self.users.all()


    def resolve_user_count(self, info, **kwargs):
        return self.members.count()
            

    def resolve_public_collections(self, info, **kwargs):
        return self.collections.filter(private=False)
    

    def resolve_collections(self, info, **kwargs):
        return self.collections.viewable_by(info.context.user)


    def resolve_collection_permission(self, info, **kwargs):
        collection = Collection.objects.filter(
            id=kwargs["id"]
        ).viewable_by(info.context.user).first()
        link = CollectionGroupLink.objects.filter(group=self, collection=collection).first()
        return link.permission if link else 0
    

    def resolve_shareable_collections(self, info, **kwargs):
        return self.shareable_collections.viewable_by(info.context.user)
    

    def resolve_editable_collections(self, info, **kwargs):
        return self.editable_collections.viewable_by(info.context.user)




class CollectionType(DjangoObjectType):
    
    class Meta:
        model = Collection
    
    id = graphene.ID()
    papers = graphene.List("core.queries.PaperType")
    samples = graphene.List("core.queries.SampleType")
    executions = graphene.List("core.queries.ExecutionType")
    sample_count = graphene.Int()
    execution_count = graphene.Int()
    can_edit = graphene.Boolean()
    can_share = graphene.Boolean()
    is_owner = graphene.Boolean()
    owners = graphene.List("core.queries.UserType")
    sharers = graphene.List("core.queries.UserType")
    editors = graphene.List("core.queries.UserType")
    group_sharers = graphene.List("core.queries.GroupType")
    group_editors = graphene.List("core.queries.GroupType")

    def resolve_papers(self, info, **kwargs):
        return self.papers.all()


    def resolve_samples(self, info, **kwargs):
        return self.samples.all().viewable_by(info.context.user)


    def resolve_executions(self, info, **kwargs):
        return (Execution.objects.filter(collection=self) | 
            Execution.objects.filter(sample__collection=self)
        ).distinct().viewable_by(info.context.user)
    

    def resolve_sample_count(self, info, **kwargs):
        return self.samples.count()


    def resolve_execution_count(self, info, **kwargs):
        return self.executions.count()
    

    def resolve_can_edit(self, info, **kwargs):
        if info.context.user:
            return self in info.context.user.editable_collections or any(
                group in self.group_editors for group in info.context.user.memberships
            )
        return False
    

    def resolve_can_share(self, info, **kwargs):
        if info.context.user:
            return self in info.context.user.shareable_collections or any(
                group in self.group_sharers for group in info.context.user.memberships
            )
        return False
    

    def resolve_is_owner(self, info, **kwargs):
        if info.context.user:
            return self in info.context.user.owned_collections
        return False



class CollectionConnection(Connection):

    class Meta:
        node = CollectionType
    
    count = graphene.Int()

    def resolve_count(self, info, **kwargs):
        return len(self.iterable)



class PaperType(DjangoObjectType):
    
    class Meta:
        model = Paper
    
    id = graphene.ID()



class SampleType(DjangoObjectType):
    
    class Meta:
        model = Sample
    
    id = graphene.ID()
    can_edit = graphene.Boolean()
    can_share = graphene.Boolean()
    is_owner = graphene.Boolean()
    executions = graphene.List("core.queries.ExecutionType")
    sharers = graphene.List("core.queries.UserType")
    editors = graphene.List("core.queries.UserType")

    def resolve_can_edit(self, info, **kwargs):
        if info.context.user:
            return self in info.context.user.editable_samples or any(
                group in self.collection.group_editors for group in info.context.user.memberships
            ) or self.collection in info.context.user.editable_collections
        return False
    

    def resolve_can_share(self, info, **kwargs):
        if info.context.user:
            return self in info.context.user.shareable_samples or any(
                group in self.collection.group_sharers for group in info.context.user.memberships
            ) or self.collection in info.context.user.shareable_collections
        return False
    

    def resolve_is_owner(self, info, **kwargs):
        if info.context.user:
            return self.collection in info.context.user.owned_collections
        return False


    def resolve_executions(self, info, **kwargs):
        return self.executions.all().viewable_by(info.context.user)



class SampleConnection(Connection):

    class Meta:
        node = SampleType
    
    count = graphene.Int()

    def resolve_count(self, info, **kwargs):
        return len(self.iterable)



class ExecutionType(DjangoObjectType):
    
    class Meta:
        model = Execution
    
    id = graphene.ID()
    terminal = graphene.String()
    command = graphene.Field("core.queries.CommandType")
    can_edit = graphene.Boolean()
    can_share = graphene.Boolean()
    is_owner = graphene.Boolean()
    owners = graphene.List("core.queries.UserType")
    sharers = graphene.List("core.queries.UserType")
    editors = graphene.List("core.queries.UserType")
    parent = graphene.Field("core.queries.ExecutionType")
    upstream= graphene.List("core.queries.ExecutionType")
    downstream_executions = graphene.List("core.queries.ExecutionType")
    component_executions = graphene.List("core.queries.ExecutionType")

    def resolve_terminal(self, info, **kwargs):
        try:
            with open(os.path.join(settings.DATA_ROOT, str(self.id), "output.txt")) as f:
                return f.read()
        except FileNotFoundError:
            try:
                with open(os.path.join(settings.DATA_ROOT, str(self.id), "stdout.txt")) as f:
                    return f.read()
            except FileNotFoundError: return ""


    def resolve_can_edit(self, info, **kwargs):
        if info.context.user:
            if self in info.context.user.editable_executions: return True
            if self.sample:
                if self.sample in info.context.user.editable_samples: return True
            collection = self.collection or (self.sample and self.sample.collection)
            if collection:
                if collection in info.context.user.editable_collections: return True
                if any(
                    group in collection.group_editors for group in info.context.user.memberships
                ): return True
        return False
    

    def resolve_can_share(self, info, **kwargs):
        if info.context.user:
            if self in info.context.user.shareable_executions: return True
            if self.sample:
                if self.sample in info.context.user.shareable_samples: return True
            collection = self.collection or (self.sample and self.sample.collection)
            if collection:
                if collection in info.context.user.shareable_collections: return True
                if any(
                    group in collection.group_sharers for group in info.context.user.memberships
                ): return True
        return False
    

    def resolve_is_owner(self, info, **kwargs):
        if info.context.user:
            if self in info.context.user.owned_executions: return True
            collection = self.collection or (self.sample and self.sample.collection)
            if collection and collection in info.context.user.owned_collections: return True
        return False


    def resolve_upstream(self, info, **kwargs):
        return self.upstream.all()


    def resolve_upstream_executions(self, info, **kwargs):
        return self.upstream.viewable_by(info.context.user)
    

    def resolve_downstream_executions(self, info, **kwargs):
        return self.downstream.viewable_by(info.context.user)
    

    def resolve_component_executions(self, info, **kwargs):
        return self.components.viewable_by(info.context.user)
    

    def resolve_collection(self, info, **kwargs):
        return self.collection or (self.sample.collection if self.sample else None)



class ExecutionConnection(Connection):

    class Meta:
        node = ExecutionType
    
    count = graphene.Int()

    def resolve_count(self, info, **kwargs):
        return len(self.iterable)


class CommandType(DjangoObjectType):
    
    class Meta:
        model = Command
    
    id = graphene.ID()
    input_schema = graphene.String()

    def resolve_input_schema(self, info, **kwargs):
        with open(os.path.join(settings.NF_ROOT, self.nextflow, "schema.json")) as f:
            return json.dumps(json.load(f)["inputs"])



class SearchType(graphene.ObjectType):

    collections = graphene.List(CollectionType)
    samples = graphene.List(SampleType)
    executions = graphene.List(ExecutionType)
    groups = graphene.List(GroupType)
    users = graphene.List(UserType)

    def resolve_collections(self, info, **kwargs):
        return (
            Collection.objects.filter(name__icontains=self["query"])
          | Collection.objects.filter(description__icontains=self["query"])
        ).distinct().viewable_by(info.context.user)
    

    def resolve_samples(self, info, **kwargs):
        return (
            Sample.objects.filter(name__icontains=self["query"])
          | Sample.objects.filter(organism__icontains=self["query"])
        ).distinct().viewable_by(info.context.user)
    

    def resolve_executions(self, info, **kwargs):
        return Execution.objects.filter(name__icontains=self["query"]).viewable_by(info.context.user)
    

    def resolve_groups(self, info, **kwargs):
        return (
            Group.objects.filter(name__icontains=self["query"])
          | Group.objects.filter(description__icontains=self["query"])
        ).distinct()
    

    def resolve_users(self, info, **kwargs):
        return User.objects.filter(name__icontains=self["query"])