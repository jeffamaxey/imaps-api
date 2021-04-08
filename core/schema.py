import graphene
from graphql import GraphQLError
from graphene.relay import ConnectionField
from core.mutations import *

class Query(graphene.ObjectType):

    access_token = graphene.String()
    user = graphene.Field("core.queries.UserType", username=graphene.String())
    users = graphene.List("core.queries.UserType")
    group = graphene.Field("core.queries.GroupType", slug=graphene.String(required=True))
    collection = graphene.Field("core.queries.CollectionType", id=graphene.ID())
    user_collections = graphene.List("core.queries.CollectionType")
    sample = graphene.Field("core.queries.SampleType", id=graphene.ID())
    execution = graphene.Field("core.queries.ExecutionType", id=graphene.ID())


    def resolve_access_token(self, info, **kwargs):
        token = info.context.COOKIES.get("refresh_token")
        if not token:
            raise GraphQLError(json.dumps({"token": "No refresh token supplied"}))
        user = User.from_token(token)
        if user:
            info.context.refresh_token = user.make_refresh_jwt()
            return user.make_access_jwt()
        raise GraphQLError(json.dumps({"token": "Refresh token not valid"}))


    def resolve_user(self, info, **kwargs):
        if "username" in kwargs:
            try:
                return User.objects.get(username=kwargs["username"])
            except: raise GraphQLError('{"user": "Does not exist"}')
        user = info.context.user
        if not user: raise GraphQLError('{"user": "Not authorized"}')
        return info.context.user
    

    def resolve_users(self, info, **kwargs):
        return User.objects.all()
    

    def resolve_group(self, info, **kwargs):
        try:
            return Group.objects.get(slug=kwargs["slug"])
        except: raise GraphQLError('{"group": "Does not exist"}')
    

    def resolve_collection(self, info, **kwargs):
        collections = Collection.objects.all().viewable_by(info.context.user)
        collection = collections.filter(id=kwargs["id"]).first()
        if collection: return collection
        raise GraphQLError('{"collection": "Does not exist"}')


    def resolve_public_collection_count(self, info, **kwargs):
        return Collection.objects.filter(private=False).count()
    

    def resolve_user_collections(self, info, **kwargs):
        return Collection.objects.all().viewable_by(info.context.user)


    def resolve_public_collections(self, info, **kwargs):
        collections = Collection.objects.filter(private=False)
        if "offset" in kwargs: collections = collections[kwargs["offset"]:]
        return collections
    

    def resolve_sample(self, info, **kwargs):
        samples = Sample.objects.all().viewable_by(info.context.user)
        sample = samples.filter(id=kwargs["id"]).first()
        if sample: return sample
        raise GraphQLError('{"sample": "Does not exist"}')
    

    def resolve_execution(self, info, **kwargs):
        executions = Execution.objects.all().viewable_by(info.context.user)
        execution = executions.filter(id=kwargs["id"]).first()
        if execution: return execution
        raise GraphQLError('{"execution": "Does not exist"}')




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
    update_group = UpdateGroupMutation.Field()
    delete_group = DeleteGroupMutation.Field()
    invite_user_to_group = InviteUserToGroup.Field()
    delete_group_invitation = DeleteGroupInvitationMutation.Field()
    accept_group_invitation = AcceptGroupInvitationMutation.Field()
    make_group_admin = MakeGroupAdminMutation.Field()
    revoke_group_admin = RevokeGroupAdminMutation.Field()
    remove_user_from_group = RemoveUserFromGroup.Field()
    leave_group = LeaveGroup.Field()

schema = graphene.Schema(query=Query, mutation=Mutation)