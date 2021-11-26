import graphene
from graphene.relay.connection import Connection
from graphene_django import DjangoObjectType
from graphql import execution
from core.permissions import  does_user_have_permission_on_collection, does_user_have_permission_on_sample, get_users_by_collection

from .models import Collection, Job, Sample, Paper
from django_nextflow.models import Data, Execution, Pipeline, ProcessExecution

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
        return Job.objects.filter(collection=self)
    
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
    
    def resolve_executions(self, info, **kwargs):
        return Job.objects.filter(sample=self)
    
    def resolve_all_data(self, info, **kwargs):
        return self.all_data.all()



class ExecutionType(DjangoObjectType):

    class Meta:
        model  = Job
    
    id = graphene.ID()
    is_owner = graphene.Boolean()
    can_share = graphene.Boolean()
    can_edit = graphene.Boolean()
    status = graphene.String()
    stdout = graphene.String()
    stderr = graphene.String()
    pipeline = graphene.Field("analysis.queries.PipelineType")
    process_executions = graphene.List("analysis.queries.ProcessExecutionType")
    upstream_data = graphene.List("analysis.queries.DataType")

    def resolve_status(self, info, **kwargs):
        print(self)
        if self.execution: return self.execution.status
    

    def resolve_stdout(self, info, **kwargs):
        if self.execution: return self.execution.stdout
    

    def resolve_stderr(self, info, **kwargs):
        if self.execution: return self.execution.stderr


    def resolve_pipeline(self, info, **kwargs):
        return self.pipeline
    

    def resolve_process_executions(self, info, **kwargs):
        if self.execution:
            return self.execution.process_executions.all()
        else: return []
    

    def resolve_upstream_data(self, info, **kwargs):
        if self.execution:
            return self.execution.upstream_data.all()
        else: return []


class ProcessExecutionType(DjangoObjectType):

    class Meta:
        model  = ProcessExecution
    
    id = graphene.ID()
    execution = graphene.Field("analysis.queries.ExecutionType")

    def resolve_execution(self, info, **kwargs):
        return self.execution.job



class DataType(DjangoObjectType):

    class Meta:
        model  = Data
    
    id = graphene.ID()
    size = graphene.Float()
    downstream_executions = graphene.List("analysis.queries.ExecutionType")

    def resolve_downstream_executions(self, info, **kwargs):
        return Job.objects.filter(execution__upstream_data=self)



class PipelineType(DjangoObjectType):

    class Meta:
        model  = Pipeline
    
    id = graphene.ID()
    input_schema = graphene.JSONString()