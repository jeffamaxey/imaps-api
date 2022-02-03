from django_nextflow.models import Data
import graphene
from graphene_django.types import DjangoObjectType
from .models import User, Group
from .permissions import does_user_have_permission_on_collection, does_user_have_permission_on_data, does_user_have_permission_on_job, does_user_have_permission_on_sample, get_collections_by_group, get_groups_by_user, get_users_by_group, readable_data, readable_jobs
from .permissions import get_collections_by_user
from .permissions import  get_data_by_user
from .permissions import readable_collections, readable_samples
from analysis.models import Collection, DataUserLink, Job, Sample, CollectionUserLink, CollectionGroupLink, SampleUserLink, JobUserLink
from analysis.queries import CollectionType, SampleType, ExecutionType, DataType

class UserType(DjangoObjectType):
    
    class Meta:
        model = User
        exclude_fields = ["password"]

    id = graphene.ID()
    admin_groups = graphene.List("core.queries.GroupType")
    memberships = graphene.List("core.queries.GroupType")
    invitations = graphene.List("core.queries.GroupType")
    collections = graphene.List("analysis.queries.CollectionType")
    data = graphene.List("analysis.queries.DataType")
    collection_permission = graphene.Int(id=graphene.ID(required=True))
    sample_permission = graphene.Int(id=graphene.ID(required=True))
    execution_permission = graphene.Int(id=graphene.ID(required=True))
    data_permission = graphene.Int(id=graphene.ID(required=True))

    def resolve_email(self, info, **kwargs):
        return self.email if info.context.user == self else ""
    
    def resolve_last_login(self, info, **kwargs):
        return self.last_login if info.context.user == self else None

    def resolve_admin_groups(self, info, **kwargs):
        return get_groups_by_user(self, 3)
    
    def resolve_memberships(self, info, **kwargs):
        return get_groups_by_user(self, 2, exact=False)
    
    def resolve_invitations(self, info, **kwargs):
        return get_groups_by_user(self, 1)
    
    def resolve_collections(self, info, **kwargs):
        return readable_collections(get_collections_by_user(self, 4), info.context.user)
    
    def resolve_collection_permission(self, info, **kwargs):
        collection = Collection.objects.filter(id=kwargs["id"]).first()
        if not does_user_have_permission_on_collection(info.context.user, collection, 1):
            return 0
        link = CollectionUserLink.objects.filter(user=self, collection=collection).first()
        return link.permission if link else 0
    
    def resolve_sample_permission(self, info, **kwargs):
        sample = Sample.objects.filter(id=kwargs["id"]).first()
        if not does_user_have_permission_on_sample(info.context.user, sample, 1):
            return 0
        link = SampleUserLink.objects.filter(user=self, sample=sample).first()
        return link.permission if link else 0
    
    def resolve_execution_permission(self, info, **kwargs):
        job = Job.objects.filter(id=kwargs["id"]).first()
        if not does_user_have_permission_on_job(info.context.user, job, 1):
            return 0
        link = JobUserLink.objects.filter(user=self, job=job).first()
        return link.permission if link else 0
    

    def resolve_data_permission(self, info, **kwargs):
        data = Data.objects.filter(id=kwargs["id"]).first()
        if not does_user_have_permission_on_data(info.context.user, data, 1):
            return 0
        link = DataUserLink.objects.filter(user=self, data=data).first()
        return link.permission if link else 0

    



class GroupType(DjangoObjectType):
    
    class Meta:
        model = Group
    
    id = graphene.ID()
    user_count = graphene.Int()
    admins = graphene.List("core.queries.UserType")
    members = graphene.List("core.queries.UserType")
    invitees = graphene.List("core.queries.UserType")
    collections = graphene.List("analysis.queries.CollectionType")
    collection_permission = graphene.Int(id=graphene.ID(required=True))

    def resolve_user_count(self, info, **kwargs):
        return get_users_by_group(self, 2, exact=False).count()
    
    def resolve_admins(self, info, **kwargs):
        return get_users_by_group(self, 3)
    
    def resolve_members(self, info, **kwargs):
        return get_users_by_group(self, 2, exact=False)

    def resolve_invitees(self, info, **kwargs):
        return get_users_by_group(self, 1)
    
    def resolve_collections(self, info, **kwargs):
        return get_collections_by_group(self, 3)
    
    def resolve_collection_permission(self, info, **kwargs):
        collection = Collection.objects.filter(id=kwargs["id"]).first()
        if not does_user_have_permission_on_collection(info.context.user, collection, 1):
            return 0
        link = CollectionGroupLink.objects.filter(group=self, collection=collection).first()
        return link.permission if link else 0



class SearchType(graphene.ObjectType):

    collections = graphene.List(CollectionType)
    samples = graphene.List(SampleType)
    executions = graphene.List(ExecutionType)
    data = graphene.List(DataType)
    groups = graphene.List(GroupType)
    users = graphene.List(UserType)

    def resolve_collections(self, info, **kwargs):
        return readable_collections(
            Collection.objects.filter(name__icontains=self["query"])
          | Collection.objects.filter(description__icontains=self["query"]),
          info.context.user
        ).distinct()[:25]
    

    def resolve_samples(self, info, **kwargs):
        return readable_samples(
            Sample.objects.filter(name__icontains=self["query"])
          | Sample.objects.filter(species__name__icontains=self["query"])
          | Sample.objects.filter(species__latin_name__icontains=self["query"]),
          info.context.user
        ).distinct()[:25]
    

    def resolve_executions(self, info, **kwargs):
        return readable_jobs(
            Job.objects.filter(execution__pipeline__name__icontains=self["query"]),
            info.context.user
        )[:25]
    

    def resolve_data(self, info, **kwargs):
        return readable_data(
            Data.objects.filter(filename__icontains=self["query"]),
            info.context.user
        )[:25]
    

    def resolve_groups(self, info, **kwargs):
        return (
            Group.objects.filter(name__icontains=self["query"])
          | Group.objects.filter(description__icontains=self["query"])
        ).distinct()[:25]
    

    def resolve_users(self, info, **kwargs):
        return User.objects.filter(name__icontains=self["query"])[:25]


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
    public_collections = graphene.List("analysis.queries.CollectionType")
    owned_collections = graphene.List("analysis.queries.CollectionType")
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
    public_collections = graphene.List("analysis.queries.CollectionType")
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
          | Sample.objects.filter(species__icontains=self["query"]),
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