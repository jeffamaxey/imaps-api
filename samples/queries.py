import graphene
from graphene.relay.connection import Connection
from graphene_django import DjangoObjectType
from core.permissions import can_user_edit_collection, can_user_share_collection, collection_owners, is_user_owner_of_collection
from core.permissions import can_user_edit_sample, can_user_share_sample, collection_owners, is_user_owner_of_sample
from .models import Collection, Sample, Paper

class CollectionType(DjangoObjectType):
    
    class Meta:
        model = Collection
    
    id = graphene.ID()
    sample_count = graphene.Int()
    execution_count = graphene.Int()
    owners = graphene.List("core.queries.UserType")
    is_owner = graphene.Boolean()
    can_share = graphene.Boolean()
    can_edit = graphene.Boolean()

    def resolve_sample_count(self, info, **kwargs):
        return self.samples.count()

    def resolve_execution_count(self, info, **kwargs):
        return self.executions.count()

    def resolve_owners(self, info, **kwargs):
        return collection_owners(self)
    
    def resolve_is_owner(self, info, **kwargs):
        return is_user_owner_of_collection(info.context.user, self)
    
    def resolve_can_share(self, info, **kwargs):
        return can_user_share_collection(info.context.user, self)
    
    def resolve_can_edit(self, info, **kwargs):
        return can_user_edit_collection(info.context.user, self)



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
    qc_pass = graphene.Boolean()
    is_owner = graphene.Boolean()
    can_share = graphene.Boolean()
    can_edit = graphene.Boolean()

    def resolve_is_owner(self, info, **kwargs):
        return is_user_owner_of_sample(info.context.user, self)
    
    def resolve_can_share(self, info, **kwargs):
        return can_user_share_sample(info.context.user, self)
    
    def resolve_can_edit(self, info, **kwargs):
        return can_user_edit_sample(info.context.user, self)