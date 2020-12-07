import graphene
from graphql import GraphQLError
from core.mutations import *

class Query(graphene.ObjectType):

    access_token = graphene.String()
    user = graphene.Field("core.queries.UserType", username=graphene.String())
    users = graphene.List("core.queries.UserType")
    group = graphene.Field("core.queries.GroupType", slug=graphene.String(required=True))
    
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




class Mutation(graphene.ObjectType):
    signup = SignupMutation.Field()
    login = LoginMutation.Field()
    logout = LogoutMutation.Field()

    update_user = UpdateUserMutation.Field()
    update_password = UpdatePasswordMutation.Field()
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