import graphene
from graphene_django.types import DjangoObjectType
from .models import User, Group
from .permissions import can_user_view_collection, can_user_view_sample
from .permissions import collections_owned_by_user, data_owned_by_user
from .permissions import group_admins, group_members
from .permissions import readable_collections, readable_samples
from .permissions import groups_run_by_user, groups_with_user_as_member
from samples.models import Collection, Sample, CollectionUserLink, CollectionGroupLink, SampleUserLink
from samples.queries import CollectionType, SampleType

class UserType(DjangoObjectType):
    
    class Meta:
        model = User
        exclude_fields = ["password"]

    id = graphene.ID()
    admin_groups = graphene.List("core.queries.GroupType")
    memberships = graphene.List("core.queries.GroupType")
    invitations = graphene.List("core.queries.GroupType")

    public_collections = graphene.List("samples.queries.CollectionType")

    public_uploads = graphene.List("samples.queries.DataType")

    def resolve_email(self, info, **kwargs):
        return self.email if info.context.user == self else ""
    
    def resolve_last_login(self, info, **kwargs):
        return self.last_login if info.context.user == self else None

    def resolve_admin_groups(self, info, **kwargs):
        return groups_run_by_user(self)
    
    def resolve_memberships(self, info, **kwargs):
        return groups_with_user_as_member(self)
    
    def resolve_invitations(self, info, **kwargs):
        return Group.objects.filter(usergrouplink__user=self, usergrouplink__permission=1)
    

    def resolve_public_collections(self, info, **kwargs):
        return collections_owned_by_user(self).filter(private=False)
    

    def resolve_public_uploads(self, info, **kwargs):
        return data_owned_by_user(self).filter(private=False, upstream_process_execution=None)



class GroupType(DjangoObjectType):
    
    class Meta:
        model = Group
    
    id = graphene.ID()



'''class UserType(DjangoObjectType):
    
    class Meta:
        model = User
        exclude_fields = ["password"]
    
    id = graphene.ID()
    admin_groups = graphene.List("core.queries.GroupType")
    memberships = graphene.List("core.queries.GroupType")
    invitations = graphene.List("core.queries.GroupType")

    collection_permission = graphene.Int(id=graphene.ID(required=True))
    sample_permission = graphene.Int(id=graphene.ID(required=True))
    execution_permission = graphene.Int(id=graphene.ID(required=True))
    public_collections = graphene.List("samples.queries.CollectionType")
    owned_collections = graphene.List("samples.queries.CollectionType")
    uploads = graphene.List("execution.queries.ExecutionType")

    def resolve_email(self, info, **kwargs):
        return self.email if info.context.user == self else ""
    
    def resolve_last_login(self, info, **kwargs):
        return self.last_login if info.context.user == self else None

    def resolve_admin_groups(self, info, **kwargs):
        return groups_run_by_user(self)
    
    def resolve_memberships(self, info, **kwargs):
        return groups_with_user_as_member(self)
    
    def resolve_invitations(self, info, **kwargs):
        return Group.objects.filter(usergrouplink__user=self, usergrouplink__permission=1)
    
    def resolve_collection_permission(self, info, **kwargs):
        collection = Collection.objects.filter(id=kwargs["id"]).first()
        if not can_user_view_collection(info.context.user, collection): return 0
        link = CollectionUserLink.objects.filter(user=self, collection=collection).first()
        return link.permission if link else 0
    
    def resolve_sample_permission(self, info, **kwargs):
        sample = Sample.objects.filter(id=kwargs["id"]).first()
        if not can_user_view_sample(info.context.user, sample): return 0
        link = SampleUserLink.objects.filter(user=self, sample=sample).first()
        return link.permission if link else 0
    
    def resolve_execution_permission(self, info, **kwargs):
        execution = Execution.objects.filter(id=kwargs["id"]).first()
        if not can_user_view_execution(info.context.user, execution): return 0
        link = ExecutionUserLink.objects.filter(user=self, execution=execution).first()
        return link.permission if link else 0
    
    def resolve_public_collections(self, info, **kwargs):
        return collections_owned_by_user(self).filter(private=False)
    
    def resolve_owned_collections(self, info, **kwargs):
        return collections_owned_by_user(self)

    def resolve_uploads(self, info, **kwargs):
        return readable_executions(executions_owned_by_user(self), info.context.user)



class GroupType(DjangoObjectType):
    
    class Meta:
        model = Group
    
    id = graphene.ID()
    user_count = graphene.Int()
    admins = graphene.List("core.queries.UserType")
    members = graphene.List("core.queries.UserType")
    invitees = graphene.List("core.queries.UserType")
    public_collections = graphene.List("samples.queries.CollectionType")
    collection_permission = graphene.Int(id=graphene.ID(required=True))

    def resolve_user_count(self, info, **kwargs):
        return group_members(self).count()

    def resolve_admins(self, info, **kwargs):
        return group_admins(self)
    
    def resolve_members(self, info, **kwargs):
        return group_members(self)
    
    def resolve_invitees(self, info, **kwargs):
        return User.objects.filter(usergrouplink__group=self, usergrouplink__permission=1)
    
    def resolve_public_collections(self, info, **kwargs):
        return self.collections.filter(private=False)
    
    def resolve_collection_permission(self, info, **kwargs):
        collection = Collection.objects.filter(id=kwargs["id"]).first()
        if not can_user_view_collection(info.context.user, collection): return 0
        link = CollectionGroupLink.objects.filter(group=self, collection=collection).first()
        return link.permission if link else 0



class SearchType(graphene.ObjectType):

    collections = graphene.List(CollectionType)
    samples = graphene.List(SampleType)
    executions = graphene.List(ExecutionType)
    groups = graphene.List(GroupType)
    users = graphene.List(UserType)

    def resolve_collections(self, info, **kwargs):
        return readable_collections(
            Collection.objects.filter(name__icontains=self["query"])
          | Collection.objects.filter(description__icontains=self["query"]),
          info.context.user
        ).distinct()
    

    def resolve_samples(self, info, **kwargs):
        return readable_samples(
            Sample.objects.filter(name__icontains=self["query"])
          | Sample.objects.filter(organism__icontains=self["query"]),
          info.context.user
        ).distinct()
    

    def resolve_executions(self, info, **kwargs):
        return readable_executions(
            Execution.objects.filter(name__icontains=self["query"]),
            info.context.user
        )
    

    def resolve_groups(self, info, **kwargs):
        return (
            Group.objects.filter(name__icontains=self["query"])
          | Group.objects.filter(description__icontains=self["query"])
        ).distinct()
    

    def resolve_users(self, info, **kwargs):
        return User.objects.filter(name__icontains=self["query"])'''