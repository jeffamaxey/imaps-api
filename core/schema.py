import graphene
from graphql import GraphQLError
from graphene.relay import ConnectionField
from core.permissions import can_user_view_collection, can_user_view_sample
from core.mutations import *
from analysis.mutations import *
from analysis.models import Collection, Sample

class Query(graphene.ObjectType):

    access_token = graphene.String()
    me = graphene.Field("core.queries.UserType")
    user = graphene.Field("core.queries.UserType", username=graphene.String(required=True))

    '''user = graphene.Field("core.queries.UserType", username=graphene.String(required=True))
    users = graphene.List("core.queries.UserType")
    group = graphene.Field("core.queries.GroupType", slug=graphene.String(required=True))
    groups = graphene.List("core.queries.GroupType")

    public_collections = ConnectionField("analysis.queries.CollectionConnection")
    user_collections = graphene.List("core.queries.CollectionType")

    collection = graphene.Field("analysis.queries.CollectionType", id=graphene.ID())
    sample = graphene.Field("core.queries.SampleType", id=graphene.ID())
    execution = graphene.Field("core.queries.ExecutionType", id=graphene.ID())
    executions = graphene.List(
        "execution.queries.ExecutionType",
        first=graphene.Int(),
        data_type=graphene.String(),
        name=graphene.String(),
    )

    command = graphene.Field("execution.queries.CommandType", id=graphene.ID())
    commands = graphene.List("execution.queries.CommandType")

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
    

    '''def resolve_users(self, info, **kwargs):
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
        collections = Collection.objects.filter(collectionuserlink__user=info.context.user)
        for group in info.context.user.groups.all():
            collections |= Collection.objects.filter(groups=group)
        return collections.distinct()
    

    def resolve_collection(self, info, **kwargs):
        collection = Collection.objects.filter(id=kwargs["id"]).first()
        if collection and can_user_view_collection(info.context.user, collection): return collection
        raise GraphQLError('{"collection": "Does not exist"}')
    

    def resolve_sample(self, info, **kwargs):
        sample = Sample.objects.filter(id=kwargs["id"]).first()
        if sample and can_user_view_sample(info.context.user, sample): return sample
        raise GraphQLError('{"sample": "Does not exist"}')
    

    def resolve_execution(self, info, **kwargs):
        execution = Execution.objects.filter(id=kwargs["id"]).first()
        if execution and can_user_view_execution(info.context.user, execution): return execution
        raise GraphQLError('{"execution": "Does not exist"}')
    

    def resolve_executions(self, info, **kwargs):
        executions = readable_executions(Execution.objects.all(), info.context.user)
        executions = executions.filter(command__output_type__contains=kwargs["data_type"])
        executions = executions.filter(name__icontains=kwargs["name"])
        if kwargs.get("first"): executions = executions[:kwargs["first"]]
        return executions
    

    def resolve_command(self, info, **kwargs):
        command = Command.objects.filter(id=kwargs["id"]).first()
        if command: return command
        raise GraphQLError('{"command": "Does not exist"}')
    

    def resolve_commands(self, info, **kwargs):
        return Command.objects.exclude(nextflow="").exclude(nextflow=None).exclude(category="internal-import")
    

    def resolve_quick_search(self, info, **kwargs):
        if len(kwargs["query"]) < 3: return None
        return kwargs'''



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

    leave_group = LeaveGroupMutation.Field()

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