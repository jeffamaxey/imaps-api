from core.permissions import can_user_edit_collection, can_user_edit_execution, can_user_edit_sample, can_user_share_collection, can_user_share_execution, can_user_share_sample, collection_owners, execution_owners, is_user_owner_of_collection, is_user_owner_of_execution, is_user_owner_of_sample, readable_collections, readable_executions, readable_samples
import graphene
import json
from graphql import GraphQLError
from graphene_file_upload.scalars import Upload
from core.models import User
from core.arguments import create_mutation_arguments
from samples.models import Sample, SampleUserLink
from execution.forms import ExecutionForm
from execution.models import Execution, ExecutionUserLink, Command
from .celery import run_command

class UpdateExecutionMutation(graphene.Mutation):

    Arguments = create_mutation_arguments(ExecutionForm, edit=True)
    
    execution = graphene.Field("core.queries.ExecutionType")

    def mutate(self, info, **kwargs):
        if not info.context.user: raise GraphQLError(json.dumps({"error": "Not authorized"}))
        execution = readable_executions(Execution.objects.filter(id=kwargs["id"]), info.context.user).first()
        if not execution: raise GraphQLError('{"execution": ["Does not exist"]}')
        if not can_user_edit_execution(info.context.user, execution):
            raise GraphQLError('{"execution": ["You don\'t have permission to edit this execution"]}')
        form = ExecutionForm(kwargs, instance=execution)
        if form.is_valid():
            form.save()
            return UpdateExecutionMutation(execution=form.instance)
        raise GraphQLError(json.dumps(form.errors))



class DeleteExecutionMutation(graphene.Mutation):

    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()

    def mutate(self, info, **kwargs):
        if not info.context.user: raise GraphQLError(json.dumps({"error": "Not authorized"}))
        execution = readable_executions(Execution.objects.filter(id=kwargs["id"]), info.context.user).first()
        if not execution: raise GraphQLError('{"execution": ["Does not exist"]}')
        if not is_user_owner_of_execution(info.context.user, execution):
            raise GraphQLError('{"execution": ["Not an owner"]}')
        execution.delete()
        return DeleteExecutionMutation(success=True)



class UpdateExecutionAccessMutation(graphene.Mutation):

    class Arguments:
        id = graphene.ID(required=True)
        user = graphene.ID()
        permission = graphene.Int(required=True)
    
    execution = graphene.Field("core.queries.ExecutionType")
    user = graphene.Field("core.queries.UserType")

    def mutate(self, info, **kwargs):
        if not info.context.user: raise GraphQLError(json.dumps({"error": "Not authorized"}))
        execution = readable_executions(
            Execution.objects.filter(id=kwargs["id"]), info.context.user
        ).first()
        if not execution: raise GraphQLError('{"execution": ["Does not exist"]}')
        if not can_user_share_execution(info.context.user, execution):
            raise GraphQLError('{"execution": ["You do not have share permissions"]}')
        user = User.objects.filter(id=kwargs.get("user")).first()
        if kwargs.get("user") and not user: raise GraphQLError('{"user": ["Does not exist"]}')
        if not 0 <= kwargs["permission"] <= 4:
            raise GraphQLError('{"permission": ["Not a valid permission"]}')
        link = ExecutionUserLink.objects.get_or_create(
            execution=execution, user=user
        )[0]
        if kwargs["permission"] == 4 and info.context.user not in execution_owners(execution):
            raise GraphQLError('{"execution": ["Only an owner can make owners"]}')
        if link.permission == 4 and info.context.user not in execution_owners(execution):
            raise GraphQLError('{"execution": ["Only an owner can remove owners"]}')
        if kwargs["permission"] == 0:
            link.delete()
        else:
            link.permission = kwargs["permission"]
            link.save()
        return UpdateExecutionAccessMutation(user=user, execution=execution)



class RunCommandMutation(graphene.Mutation):

    class Arguments:
        command = graphene.ID(required=True)
        inputs = graphene.String(required=True)
        uploads = graphene.List(Upload)
        create_sample = graphene.Boolean()

    execution = graphene.Field("core.queries.ExecutionType")

    def mutate(self, info, **kwargs):
        if not info.context.user:
            raise GraphQLError(json.dumps({"error": "Not authorized"}))
        command = Command.objects.get(id=kwargs["command"])
        if command.category == "import":
            upload_name = json.loads(kwargs["inputs"])[0]["value"]["file"]
        collection = None
        sample = None
        if command.can_create_sample and kwargs.get("create_sample"):
            sample = Sample.objects.create(
                name=upload_name,
                collection=collection
            )
            SampleUserLink.objects.create(user=info.context.user, sample=sample, permission=3)
        name = command.name
        if command.category == "import":
            name = f"Upload: {upload_name}"
        execution = Execution.objects.create(
            name=name, command=command,
            input=kwargs["inputs"], output="[]",
            collection=collection, sample=sample,
        )
        execution.prepare_directory(kwargs.get("uploads", []))
        ExecutionUserLink.objects.create(user=info.context.user, execution=execution, permission=4)
        run_command.apply_async((execution.id,), task_id=str(execution.id))
        return RunCommandMutation(execution=execution)