from django_nextflow.models import Data, Pipeline
from core.permissions import readable_collections, readable_samples
import graphene
import json
from graphql import GraphQLError
from graphene_file_upload.scalars import Upload
from core.models import User, Group
from core.arguments import create_mutation_arguments
from analysis.models import Collection, CollectionUserLink, CollectionGroupLink, DataLink, DataUserLink, Job, JobUserLink, Sample, SampleUserLink
from analysis.forms import CollectionForm, PaperForm, SampleForm
from analysis.celery import run_pipeline

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
        if not info.context.user: raise GraphQLError(json.dumps({"error": "Not authorized"}))
        collection = readable_collections(
            Collection.objects.filter(id=kwargs["id"]), info.context.user
        ).first()
        if not collection: raise GraphQLError('{"collection": ["Does not exist"]}')
        if not can_user_edit_collection(info.context.user, collection):
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



class DeleteCollectionMutation(graphene.Mutation):

    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()

    def mutate(self, info, **kwargs):
        if not info.context.user: raise GraphQLError(json.dumps({"error": "Not authorized"}))
        collection = readable_collections(Collection.objects.filter(id=kwargs["id"]), info.context.user).first()
        if not collection: raise GraphQLError('{"collection": ["Does not exist"]}')
        if not is_user_owner_of_collection(info.context.user, collection):
            raise GraphQLError('{"collection": ["Not an owner"]}')
        executions = (
            Execution.objects.filter(collection=collection) |
            Execution.objects.filter(sample__collection=collection)
        )
        executions.delete()
        collection.samples.all().delete()
        collection.delete()
        return DeleteCollectionMutation(success=True)



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


        collection = readable_collections(Collection.objects.filter(id=kwargs["id"]), info.context.user).first()
        if not collection: raise GraphQLError('{"collection": ["Does not exist"]}')
        if not can_user_share_collection(info.context.user, collection):
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
            if kwargs["permission"] == 4 and not is_user_owner_of_collection(info.context.user, collection):
                raise GraphQLError('{"collection": ["Only an owner can make owners"]}')
            if link.permission == 4 and not is_user_owner_of_collection(info.context.user, collection):
                raise GraphQLError('{"collection": ["Only an owner can remove owners"]}')
            if collection_owners(collection).count() == 1 and link.permission == 4 and kwargs["permission"] != 4:
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



class UpdateSampleMutation(graphene.Mutation):

    Arguments = create_mutation_arguments(
        SampleForm, edit=True, collection=graphene.ID()
    )
    
    sample = graphene.Field("core.queries.SampleType")

    def mutate(self, info, **kwargs):
        if not info.context.user: raise GraphQLError(json.dumps({"error": "Not authorized"}))
        sample = readable_samples(Sample.objects.filter(id=kwargs["id"]), info.context.user).first()
        if not sample: raise GraphQLError('{"sample": ["Does not exist"]}')
        collection = readable_collections(Collection.objects.filter(id=kwargs.get("collection")), info.context.user).first()
        if not collection and sample.collection: raise GraphQLError('{"collection": ["Does not exist"]}')
        if collection and not is_user_owner_of_collection(info.context.user, collection):
            raise GraphQLError('{"sample": ["The new collection is not owned by you"]}')
        if not can_user_edit_sample(info.context.user, sample):
            raise GraphQLError('{"sample": ["You don\'t have permission to edit this sample"]}')
        if not collection: kwargs["collection"] = None
        form = SampleForm(kwargs, instance=sample)
        if form.is_valid():
            form.save()
            form.instance.collection = collection
            form.instance.save()
            return UpdateSampleMutation(sample=form.instance)
        raise GraphQLError(json.dumps(form.errors))



class DeleteSampleMutation(graphene.Mutation):

    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()

    def mutate(self, info, **kwargs):
        if not info.context.user:
            raise GraphQLError(json.dumps({"error": "Not authorized"}))
        sample = readable_samples(Sample.objects.filter(id=kwargs["id"]), info.context.user).first()
        if not sample: raise GraphQLError('{"sample": ["Does not exist"]}')
        if not is_user_owner_of_sample(info.context.user, sample):
            raise GraphQLError('{"sample": ["Not an owner"]}')
        executions = Execution.objects.filter(sample=sample)
        executions.delete()
        sample.delete()
        return DeleteSampleMutation(success=True)



class UpdateSampleAccessMutation(graphene.Mutation):

    class Arguments:
        id = graphene.ID(required=True)
        user = graphene.ID()
        permission = graphene.Int(required=True)
    
    sample = graphene.Field("samples.queries.SampleType")
    user = graphene.Field("core.queries.UserType")

    def mutate(self, info, **kwargs):
        if not info.context.user: raise GraphQLError(json.dumps({"error": "Not authorized"}))
        sample = readable_samples(Sample.objects.filter(id=kwargs["id"]), info.context.user).first()
        if not sample: raise GraphQLError('{"sample": ["Does not exist"]}')

        if not can_user_share_sample(info.context.user, sample):
            raise GraphQLError('{"sample": ["You do not have share permissions"]}')
        user = User.objects.filter(id=kwargs.get("user")).first()
        if kwargs.get("user") and not user: raise GraphQLError('{"user": ["Does not exist"]}')
        if not 0 <= kwargs["permission"] <= 3:
            raise GraphQLError('{"permission": ["Not a valid permission"]}')
        link = SampleUserLink.objects.get_or_create(sample=sample, user=user)[0]
        if kwargs["permission"] == 0:
            link.delete()
        else:
            link.permission = kwargs["permission"]
            link.save()
        return UpdateSampleAccessMutation(user=user, sample=sample)



class UploadDataMutation(graphene.Mutation):

    class Arguments:
        file = Upload(required=True)
        make_sample = graphene.Boolean()

    data = graphene.Field("analysis.queries.DataType")

    def mutate(self, info, **kwargs):
        print(kwargs)
        data = Data.create_from_upload(kwargs["file"])
        DataLink.objects.create(data=data)
        DataUserLink.objects.create(data=data, user=info.context.user, permission=4)
        if kwargs.get("make_sample"):
            sample = Sample.objects.create(
                name=data.filename,
                initiator=data
            )
            SampleUserLink.objects.create(sample=sample, user=info.context.user, permission=3)
        return UploadDataMutation(data=data)



class RunPipelineMutation(graphene.Mutation):

    class Arguments:
        pipeline = graphene.ID(required=True)
        inputs = graphene.String()
        dataInputs = graphene.String()

    execution = graphene.Field("analysis.queries.ExecutionType")

    def mutate(self, info, **kwargs):
        pipeline = Pipeline.objects.filter(id=kwargs["pipeline"]).first()
        job = Job.objects.create(pipeline=pipeline)
        JobUserLink.objects.create(job=job, user=info.context.user, permission=4)
        run_pipeline.apply_async((kwargs, job.id, info.context.user.id), task_id=str(job.id))
        return RunPipelineMutation(execution=job)