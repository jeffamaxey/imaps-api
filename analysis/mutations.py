from django_nextflow.models import Data, Execution, Pipeline
from core.permissions import does_user_have_permission_on_collection, does_user_have_permission_on_data, does_user_have_permission_on_job, does_user_have_permission_on_sample, get_users_by_collection, readable_collections, readable_data, readable_jobs, readable_samples
import graphene
import json
import pandas as pd
from graphql import GraphQLError
from graphene_file_upload.scalars import Upload
from core.models import User, Group
from core.arguments import create_mutation_arguments
from analysis.models import Collection, CollectionUserLink, CollectionGroupLink, DataLink, DataUserLink, Job, JobUserLink, Sample, SampleUserLink
from genomes.models import Species
from analysis.forms import CollectionForm, DataForm, PaperForm, SampleForm
from analysis.celery import run_pipeline
from genomes.annotation import validate_uploaded_sheet

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
        if not does_user_have_permission_on_collection(info.context.user, collection, 2):
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
        if not does_user_have_permission_on_collection(info.context.user, collection, 4):
            raise GraphQLError('{"collection": ["Not an owner"]}')
        '''executions = (
            Execution.objects.filter(collection=collection) |
            Execution.objects.filter(sample__collection=collection)
        )
        executions.delete()'''
        collection.samples.all().delete()
        collection.delete()
        return DeleteCollectionMutation(success=True)



class UpdateCollectionAccessMutation(graphene.Mutation):

    class Arguments:
        id = graphene.ID(required=True)
        user = graphene.ID()
        group = graphene.ID()
        permission = graphene.Int(required=True)
    
    collection = graphene.Field("analysis.queries.CollectionType")
    user = graphene.Field("core.queries.UserType")
    group = graphene.Field("core.queries.GroupType")

    def mutate(self, info, **kwargs):
        if not info.context.user: raise GraphQLError(json.dumps({"error": "Not authorized"}))


        collection = readable_collections(Collection.objects.filter(id=kwargs["id"]), info.context.user).first()
        if not collection: raise GraphQLError('{"collection": ["Does not exist"]}')
        if not does_user_have_permission_on_collection(info.context.user, collection, 3):
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
            if kwargs["permission"] == 4 and not does_user_have_permission_on_collection(info.context.user, collection, 4):
                raise GraphQLError('{"collection": ["Only an owner can make owners"]}')
            if link.permission == 4 and not does_user_have_permission_on_collection(info.context.user, collection, 4):
                raise GraphQLError('{"collection": ["Only an owner can remove owners"]}')
            if get_users_by_collection(collection, 4).count() == 1 and link.permission == 4 and kwargs["permission"] != 4:
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
        if collection and not does_user_have_permission_on_collection(info.context.user, collection, 4):
            raise GraphQLError('{"sample": ["The new collection is not owned by you"]}')
        if not does_user_have_permission_on_sample(info.context.user, sample, 2):
            raise GraphQLError('{"sample": ["You don\'t have permission to edit this sample"]}')
        if not collection: kwargs["collection"] = None
        form = SampleForm(kwargs, instance=sample)
        if form.is_valid():
            form.save()
            form.instance.collection = collection
            form.instance.save()
            return UpdateSampleMutation(sample=form.instance)
        raise GraphQLError(json.dumps(form.errors))



class UpdateSampleAccessMutation(graphene.Mutation):

    class Arguments:
        id = graphene.ID(required=True)
        user = graphene.ID()
        permission = graphene.Int(required=True)
    
    sample = graphene.Field("analysis.queries.SampleType")
    user = graphene.Field("core.queries.UserType")

    def mutate(self, info, **kwargs):
        if not info.context.user: raise GraphQLError(json.dumps({"error": "Not authorized"}))
        sample = readable_samples(Sample.objects.filter(id=kwargs["id"]), info.context.user).first()
        if not sample: raise GraphQLError('{"sample": ["Does not exist"]}')

        if not does_user_have_permission_on_sample(info.context.user, sample, 3):
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



class DeleteSampleMutation(graphene.Mutation):

    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()

    def mutate(self, info, **kwargs):
        if not info.context.user:
            raise GraphQLError(json.dumps({"error": "Not authorized"}))
        sample = readable_samples(Sample.objects.filter(id=kwargs["id"]), info.context.user).first()
        if not sample: raise GraphQLError('{"sample": ["Does not exist"]}')
        if not does_user_have_permission_on_sample(info.context.user, sample, 4):
            raise GraphQLError('{"sample": ["Not an owner"]}')
        executions = Job.objects.filter(sample=sample)
        executions.delete()
        sample.delete()
        return DeleteSampleMutation(success=True)



class UpdateExecutionMutation(graphene.Mutation):

    class Arguments:
        id = graphene.ID(required=True)
        private = graphene.Boolean(required=True)
    
    execution = graphene.Field("analysis.queries.ExecutionType")

    def mutate(self, info, **kwargs):
        if not info.context.user: raise GraphQLError(json.dumps({"error": "Not authorized"}))
        job = readable_jobs(Job.objects.filter(id=kwargs["id"]), info.context.user).first()
        if not job: raise GraphQLError('{"execution": ["Does not exist"]}')
        if not does_user_have_permission_on_job(info.context.user, job, 2):
            raise GraphQLError('{"data": ["You don\'t have permission to edit this execution"]}')
        job.private = kwargs["private"]
        job.save()
        return UpdateExecutionMutation(execution=job)


class UpdateExecutionAccessMutation(graphene.Mutation):

    class Arguments:
        id = graphene.ID(required=True)
        user = graphene.ID()
        permission = graphene.Int(required=True)
    
    execution = graphene.Field("analysis.queries.ExecutionType")
    user = graphene.Field("core.queries.UserType")

    def mutate(self, info, **kwargs):
        if not info.context.user: raise GraphQLError(json.dumps({"error": "Not authorized"}))
        job = readable_jobs(Job.objects.filter(id=kwargs["id"]), info.context.user).first()
        if not job: raise GraphQLError('{"execution": ["Does not exist"]}')
        if not does_user_have_permission_on_job(info.context.user, job, 3):
            raise GraphQLError('{"execution": ["You do not have share permissions"]}')
        user = User.objects.filter(id=kwargs.get("user")).first()
        if kwargs.get("user") and not user: raise GraphQLError('{"user": ["Does not exist"]}')
        if not 0 <= kwargs["permission"] <= 4:
            raise GraphQLError('{"permission": ["Not a valid permission"]}')
        link = JobUserLink.objects.get_or_create(job=job, user=user)[0]
        if kwargs["permission"] == 0:
            link.delete()
        else:
            link.permission = kwargs["permission"]
            link.save()
        return UpdateExecutionAccessMutation(user=user, execution=job)



class UploadDataMutation(graphene.Mutation):

    class Arguments:
        file = Upload(required=True)
        make_sample = graphene.Boolean()
        is_multiplexed = graphene.Boolean()
        is_annotation = graphene.Boolean()
        is_directory = graphene.Boolean()
        ignore_warnings = graphene.Boolean()

    data = graphene.Field("analysis.queries.DataType")

    def mutate(self, info, **kwargs):
        if not info.context.user: raise GraphQLError(json.dumps({"error": "Not authorized"}))

        if kwargs.get("is_directory") and not kwargs["file"].name.endswith(".zip"):
            raise GraphQLError('{"file": ["If file is a directory, it must be a .zip file"]}')

        if kwargs.get("is_annotation"):
            problems, warning = validate_uploaded_sheet(
                kwargs["file"], info.context.user, kwargs.get("ignore_warnings", False)
            )
            if warning:
                raise GraphQLError(json.dumps({"warning": warning}))
            if problems:
                raise GraphQLError(json.dumps({"annotation": problems}))


        data = Data.create_from_upload(
            kwargs["file"], is_directory=kwargs.get("is_directory", False)
        )
        DataLink.objects.create(
            data=data,
            is_multiplexed=kwargs.get("is_multiplexed", False),
            is_annotation=kwargs.get("is_annotation", False),
        )
        DataUserLink.objects.create(data=data, user=info.context.user, permission=4)
        if kwargs.get("make_sample"):
            sample = Sample.objects.create(
                name=data.filename,
                initiator=data
            )
            SampleUserLink.objects.create(sample=sample, user=info.context.user, permission=3)
        return UploadDataMutation(data=data)



class UpdateDataMutation(graphene.Mutation):

    class Arguments:
        id = graphene.ID(required=True)
        private = graphene.Boolean(required=True)
    
    data = graphene.Field("analysis.queries.DataType")

    def mutate(self, info, **kwargs):
        if not info.context.user: raise GraphQLError(json.dumps({"error": "Not authorized"}))
        data = readable_data(Data.objects.filter(id=kwargs["id"]), info.context.user).first()
        if not data: raise GraphQLError('{"data": ["Does not exist"]}')
        if not does_user_have_permission_on_data(info.context.user, data, 2):
            raise GraphQLError('{"data": ["You don\'t have permission to edit this data"]}')
        data.link.private = kwargs["private"]
        data.link.save()
        return UpdateDataMutation(data=data)



class UpdateDataAccessMutation(graphene.Mutation):

    class Arguments:
        id = graphene.ID(required=True)
        user = graphene.ID()
        permission = graphene.Int(required=True)
    
    data = graphene.Field("analysis.queries.DataType")
    user = graphene.Field("core.queries.UserType")

    def mutate(self, info, **kwargs):
        if not info.context.user: raise GraphQLError(json.dumps({"error": "Not authorized"}))
        data = readable_data(Data.objects.filter(id=kwargs["id"]), info.context.user).first()
        if not data: raise GraphQLError('{"sample": ["Does not exist"]}')

        if not does_user_have_permission_on_data(info.context.user, data, 3):
            raise GraphQLError('{"data": ["You do not have share permissions"]}')
        user = User.objects.filter(id=kwargs.get("user")).first()
        if kwargs.get("user") and not user: raise GraphQLError('{"user": ["Does not exist"]}')
        if not 0 <= kwargs["permission"] <= 4:
            raise GraphQLError('{"permission": ["Not a valid permission"]}')
        link = DataUserLink.objects.get_or_create(data=data, user=user)[0]
        if kwargs["permission"] == 0:
            link.delete()
        else:
            link.permission = kwargs["permission"]
            link.save()
        return UpdateDataAccessMutation(user=user, data=data)



class RunPipelineMutation(graphene.Mutation):

    class Arguments:
        pipeline = graphene.ID(required=True)
        inputs = graphene.String()
        dataInputs = graphene.String()
        species = graphene.String()

    execution = graphene.Field("analysis.queries.ExecutionType")

    def mutate(self, info, **kwargs):
        pipeline = Pipeline.objects.filter(id=kwargs["pipeline"]).first()
        species = None
        if pipeline.link.can_produce_genome and kwargs.get("species"):
            species = Species.objects.get(id=kwargs["species"])
        job = Job.objects.create(
            pipeline=pipeline,
            params=kwargs["inputs"],
            data_params=kwargs["dataInputs"],
            species=species
        )
        print(species)
        print(species.jobs.all())
        JobUserLink.objects.create(job=job, user=info.context.user, permission=4)
        run_pipeline.apply_async((kwargs, job.id, info.context.user.id), task_id=str(job.id))
        return RunPipelineMutation(execution=job)