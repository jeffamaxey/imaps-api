import graphene
from graphene.relay.connection import Connection
from graphene_django import DjangoObjectType
from core.permissions import  does_user_have_permission_on_collection, does_user_have_permission_on_sample, get_users_by_collection

from .models import Collection, Sample, Paper
from django_nextflow.models import Data, Execution, Pipeline

class CollectionType(DjangoObjectType):
    
    class Meta:
        model = Collection
    
    id = graphene.ID()
    sample_count = graphene.Int()
    execution_count = graphene.Int()
    data_count = graphene.Int()
    owners = graphene.List("core.queries.UserType")
    all_executions = graphene.List("analysis.queries.ExecutionType")
    data = graphene.List("analysis.queries.DataType")
    all_data = graphene.List("analysis.queries.DataType")
    is_owner = graphene.Boolean()
    can_share = graphene.Boolean()
    can_edit = graphene.Boolean()

    def resolve_sample_count(self, info, **kwargs):
        return self.samples.count()

    def resolve_execution_count(self, info, **kwargs):
        return self.all_executions.count()
    
    def resolve_data_count(self, info, **kwargs):
        return self.all_data.count()

    def resolve_owners(self, info, **kwargs):
        return get_users_by_collection(self, 4)
    
    def resolve_all_executions(self, info, **kwargs):
        return self.all_executions.all()
    
    def resolve_all_data(self, info, **kwargs):
        return self.all_data.all()
    
    def resolve_is_owner(self, info, **kwargs):
        return does_user_have_permission_on_collection(info.context.user, self, 4)
    
    def resolve_can_share(self, info, **kwargs):
        return does_user_have_permission_on_collection(info.context.user, self, 3)
    
    def resolve_can_edit(self, info, **kwargs):
        return does_user_have_permission_on_collection(info.context.user, self, 2)



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
    executions = graphene.List("analysis.queries.ExecutionType")
    data = graphene.List("analysis.queries.DataType")
    all_data = graphene.List("analysis.queries.DataType")

    def resolve_is_owner(self, info, **kwargs):
        return does_user_have_permission_on_sample(info.context.user, self, 4)
    
    def resolve_can_share(self, info, **kwargs):
        return does_user_have_permission_on_sample(info.context.user, self, 3)
    
    def resolve_can_edit(self, info, **kwargs):
        return does_user_have_permission_on_sample(info.context.user, self, 2)
    
    def resolve_all_data(self, info, **kwargs):
        return self.all_data.all()



class ExecutionType(DjangoObjectType):

    class Meta:
        model  = Execution
    
    id = graphene.ID()



class DataType(DjangoObjectType):

    class Meta:
        model  = Data
    
    id = graphene.ID()



class PipelineType(DjangoObjectType):

    class Meta:
        model  = Pipeline
    
    id = graphene.ID()
    input_schema = graphene.JSONString()