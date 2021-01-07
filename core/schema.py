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
    collections = ConnectionField("core.queries.CollectionConnection")
    
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
                user = User.objects.get(username=kwargs["username"])
                user.restricted = True
                return user
            except: raise GraphQLError('{"user": "Does not exist"}')
        user = info.context.user
        if not user: raise GraphQLError('{"user": "Not authorized"}')
        user.restricted = False
        return info.context.user
    

    def resolve_users(self, info, **kwargs):
        return User.objects.all()
    

    def resolve_group(self, info, **kwargs):
        try:
            return Group.objects.get(slug=kwargs["slug"])
        except: raise GraphQLError('{"group": "Does not exist"}')
    

    def resolve_collection(self, info, **kwargs):
        collections = Collection.objects.filter(private=False)
        if info.context.user:
            collections = collections | Collection.objects.filter(owner=info.context.user)
            collections = collections | info.context.user.collections.all()
            for group in info.context.user.groups.all():
                collections = collections | group.collections.all()
        collection = collections.filter(id=kwargs["id"]).first()
        if collection: return collection
        raise GraphQLError('{"collection": "Does not exist"}')


    def resolve_collections(self, info, **kwargs):
        return Collection.objects.filter(private=False)




class Mutation(graphene.ObjectType):
    signup = SignupMutation.Field()
    login = LoginMutation.Field()
    logout = LogoutMutation.Field()

    update_user = UpdateUserMutation.Field()
    update_password = UpdatePasswordMutation.Field()
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