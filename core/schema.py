from django_nextflow.models import Data
import graphene
from graphql import GraphQLError
from graphene.relay import ConnectionField
from core.permissions import does_user_have_permission_on_collection, does_user_have_permission_on_data, does_user_have_permission_on_job, does_user_have_permission_on_sample, get_collections_by_group, get_collections_by_user, readable_data, readable_jobs
from core.mutations import *
from analysis.mutations import *
from analysis.models import Collection, Sample, Job
from django_nextflow.models import Pipeline

class Query(graphene.ObjectType):

    access_token = graphene.String()
    me = graphene.Field("core.queries.UserType")
    user = graphene.Field("core.queries.UserType", username=graphene.String(required=True))
    users = graphene.List("core.queries.UserType")
    group = graphene.Field("core.queries.GroupType", slug=graphene.String(required=True))
    groups = graphene.List("core.queries.GroupType")

    public_collections = ConnectionField("analysis.queries.CollectionConnection")
    user_collections = graphene.List("core.queries.CollectionType")

    collection = graphene.Field("analysis.queries.CollectionType", id=graphene.ID())
    sample = graphene.Field("analysis.queries.SampleType", id=graphene.ID())
    execution = graphene.Field("analysis.queries.ExecutionType", id=graphene.ID())
    data_file = graphene.Field("analysis.queries.DataType", id=graphene.ID())
    data = graphene.List(
        "analysis.queries.DataType",
        first=graphene.Int(),
        filetype=graphene.String(),
        name=graphene.String(),
    )

    pipeline = graphene.Field("analysis.queries.PipelineType", id=graphene.ID())
    pipelines = graphene.List("analysis.queries.PipelineType")

    quick_search = graphene.Field("core.queries.SearchType", query=graphene.String(required=True))


    '''
    quick_search = graphene.Field("core.queries.SearchType", query=graphene.String(required=True))'''


    def resolve_access_token(self, info, **kwargs):
        token = info.context.COOKIES.get("imaps_refresh_token")
        if not token:
            raise GraphQLError(json.dumps({"token": "No refresh token supplied"}))
        user = User.from_token(token)
        if user:
            info.context.imaps_refresh_token = user.make_jwt(31536000)
            return user.make_jwt(900)
        raise GraphQLError(json.dumps({"token": "Refresh token not valid"}))
    

    def resolve_me(self, info, **kwargs):
        return info.context.user
    

    def resolve_user(self, info, **kwargs):
        try:
            return User.objects.get(username=kwargs["username"])
        except: raise GraphQLError('{"user": "Does not exist"}')
    

    def resolve_users(self, info, **kwargs):
        return User.objects.all()
    

    def resolve_group(self, info, **kwargs):
        try:
            return Group.objects.get(slug=kwargs["slug"])
        except: raise GraphQLError('{"group": "Does not exist"}')
    

    def resolve_groups(self, info, **kwargs):
        return Group.objects.all()
    

    def resolve_public_collections(self, info, **kwargs):
        return Collection.objects.filter(private=False)
    

    def resolve_user_collections(self, info, **kwargs):
        if not info.context.user: return []
        collections = get_collections_by_user(info.context.user, 1, exact=False)
        for group in info.context.user.groups.all():
            collections |= get_collections_by_group(group, 1)
        return collections.distinct()
    

    def resolve_collection(self, info, **kwargs):
        collection = Collection.objects.filter(id=kwargs["id"]).first()
        if collection and does_user_have_permission_on_collection(info.context.user, collection, 1):
            return collection
        raise GraphQLError('{"collection": "Does not exist"}')
    

    def resolve_sample(self, info, **kwargs):
        sample = Sample.objects.filter(id=kwargs["id"]).first()
        if sample and does_user_have_permission_on_sample(info.context.user, sample,1 ):
            return sample
        raise GraphQLError('{"sample": "Does not exist"}')
    

    def resolve_execution(self, info, **kwargs):
        job = Job.objects.filter(id=kwargs["id"]).first()
        if job and does_user_have_permission_on_job(info.context.user, job, 1):
            return job
        raise GraphQLError('{"execution": "Does not exist"}')
    

    def resolve_data_file(self, info, **kwargs):
        data = Data.objects.filter(id=kwargs["id"]).first()
        if data and does_user_have_permission_on_data(info.context.user, data, 1):
            return data
        raise GraphQLError('{"data": "Does not exist"}')
    

    def resolve_pipeline(self, info, **kwargs):
        pipeline = Pipeline.objects.filter(id=kwargs["id"]).first()
        if pipeline: return pipeline
        raise GraphQLError('{"command": "Does not exist"}')
    

    def resolve_pipelines(self, info, **kwargs):
        return Pipeline.objects.exclude(path="")
    

    def resolve_quick_search(self, info, **kwargs):
        if len(kwargs["query"]) < 3: return None
        return kwargs



class Mutation(graphene.ObjectType):
    signup = SignupMutation.Field()
    login = LoginMutation.Field()
    logout = LogoutMutation.Field()

    update_user = UpdateUserMutation.Field()
    update_password = UpdatePasswordMutation.Field()
    request_password_reset = RequestPasswordResetMutation.Field()
    reset_password = ResetPasswordMutation.Field()
    update_user_image = UpdateUserImageMutation.Field()
    delete_user = DeleteUserMutation.Field()

    create_group = CreateGroupMutation.Field()
    leave_group = LeaveGroupMutation.Field()

    create_collection = CreateCollectionMutation.Field()

    '''

    create_group = CreateGroupMutation.Field()
    update_group = UpdateGroupMutation.Field()
    
    process_group_invitation = ProcessGroupInvitationMutation.Field()
    invite_user_to_group = InviteUserToGroupMutation.Field()
    make_group_admin = MakeGroupAdminMutation.Field()
    revoke_group_admin = RevokeGroupAdminMutation.Field()
    remove_user_from_group = RemoveUserFromGroupMutation.Field()
    leave_group = LeaveGroupMutation.Field()
    delete_group = DeleteGroupMutation.Field()

    create_collection = CreateCollectionMutation.Field()
    update_collection = UpdateCollectionMutation.Field()
    delete_collection = DeleteCollectionMutation.Field()
    update_collection_access = UpdateCollectionAccessMutation.Field()

    update_sample = UpdateSampleMutation.Field()
    delete_sample = DeleteSampleMutation.Field()
    update_sample_access = UpdateSampleAccessMutation.Field()

    update_execution = UpdateExecutionMutation.Field()
    delete_execution = DeleteExecutionMutation.Field()
    update_execution_access = UpdateExecutionAccessMutation.Field()

    run_command = RunCommandMutation.Field()'''



schema = graphene.Schema(query=Query, mutation=Mutation)