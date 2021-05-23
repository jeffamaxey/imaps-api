import graphene
from graphql import GraphQLError
from graphene.relay import ConnectionField
from core.mutations import *

class Query(graphene.ObjectType):

    access_token = graphene.String()
    user = graphene.Field("core.queries.UserType", username=graphene.String())
    users = graphene.List("core.queries.UserType")
    group = graphene.Field("core.queries.GroupType", slug=graphene.String(required=True))
    groups = graphene.List("core.queries.GroupType")
    collection = graphene.Field("core.queries.CollectionType", id=graphene.ID())
    sample = graphene.Field("core.queries.SampleType", id=graphene.ID())
    execution = graphene.Field("core.queries.ExecutionType", id=graphene.ID())
    quick_search = graphene.Field("core.queries.SearchType", query=graphene.String(required=True))
    public_collections = ConnectionField("core.queries.CollectionConnection")
    user_collections = graphene.List("core.queries.CollectionType")
    commands = graphene.List("core.queries.CommandType")
    command = graphene.Field("core.queries.CommandType", id=graphene.ID())
    search_collections = ConnectionField(
        "core.queries.CollectionConnection",
        query=graphene.String(required=True),
        sort=graphene.String(),
        owner=graphene.String(),
        created=graphene.String(),
    )
    search_samples = ConnectionField(
        "core.queries.SampleConnection",
        query=graphene.String(required=True),
        sort=graphene.String(),
        organism=graphene.String(),
        owner=graphene.String(),
        created=graphene.String(),
    )
    search_executions = ConnectionField(
        "core.queries.ExecutionConnection",
        query=graphene.String(required=True),
        sort=graphene.String(),
        command=graphene.String(),
        owner=graphene.String(),
        created=graphene.String(),
    )


    def resolve_access_token(self, info, **kwargs):
        token = info.context.COOKIES.get("imaps_refresh_token")
        if not token:
            raise GraphQLError(json.dumps({"token": "No refresh token supplied"}))
        user = User.from_token(token)
        if user:
            info.context.imaps_refresh_token = user.make_refresh_jwt()
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
    

    def resolve_groups(self, info, **kwargs):
        return Group.objects.all()
    

    def resolve_collection(self, info, **kwargs):
        collections = Collection.objects.all().viewable_by(info.context.user)
        collection = collections.filter(id=kwargs["id"]).first()
        if collection: return collection
        raise GraphQLError('{"collection": "Does not exist"}')


    def resolve_public_collection_count(self, info, **kwargs):
        return Collection.objects.filter(private=False).count()
    

    def resolve_user_collections(self, info, **kwargs):
        if not info.context.user: return []
        collections = Collection.objects.filter(collectionuserlink__user=info.context.user)
        for group in info.context.user.groups.all():
            collections |= Collection.objects.filter(groups=group)
        return collections.distinct()


    def resolve_public_collections(self, info, **kwargs):
        return Collection.objects.filter(private=False)
    

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
    

    def resolve_commands(self, info, **kwargs):
        commands = Command.objects.all()
        slugs = set([command.slug for command in commands])
        slug_commands = {slug: sorted([c for c in commands if c.slug == slug], key=lambda c: c.version) for slug in slugs}
        return [commands[-1] for commands in slug_commands.values()]
    

    def resolve_command(self, info, **kwargs):
        command = Command.objects.filter(id=kwargs["id"]).first()
        if command: return command
        raise GraphQLError('{"command": "Does not exist"}')


    def resolve_quick_search(self, info, **kwargs):
        query = kwargs["query"]
        if len(query) >= 3:
            results = []
            results += [{
                "name": c.name, "kind": "Collection", "pk": c.id, "match": ""
            } for c in Collection.objects.filter(name__icontains=query).viewable_by(info.context.user)]
            results += [{
                "name": c.name, "kind": "Collection", "pk": c.id,
                "match": c.description,
                "match_loc": [c.description.lower().find(query.lower()), c.description.lower().find(query.lower()) + len(query)]
            } for c in Collection.objects.filter(description__icontains=query).viewable_by(info.context.user)]
            results += [{
                "name": s.name, "kind": "Sample", "pk": s.id, "match": ""
            } for s in Sample.objects.filter(name__icontains=query).viewable_by(info.context.user)]
            results += [{
                "name": s.name, "kind": "Sample", "pk": s.id,
                "match": s.organism,
                "match_loc": [s.organism.lower().find(query.lower()), s.organism.lower().find(query.lower()) + len(query)]
            } for s in Sample.objects.filter(organism__icontains=query).viewable_by(info.context.user)]
            results += [{
                "name": e.name, "kind": "Execution", "pk": e.id, "match": ""
            } for e in Execution.objects.filter(name__icontains=query).viewable_by(info.context.user)]
            results += [{
                "name": g.name, "kind": "Group", "pk": g.slug, "match": ""
            } for g in Group.objects.filter(name__icontains=query)]
            results += [{
                "name": g.name, "kind": "Group", "pk": g.slug,
                "match": g.description,
                "match_loc": [g.description.lower().find(query.lower()), g.description.lower().find(query.lower()) + len(query)]
            } for g in Group.objects.filter(description__icontains=query)]
            results += [{
                "name": u.name, "kind": "User", "pk": u.username, "match": ""
            } for u in User.objects.filter(name__icontains=query)]
            return {"results": results}
    

    def resolve_search_collections(self, info, **kwargs):
        collections = Collection.objects.filter(
            name__icontains=kwargs["query"].lower()
        ).viewable_by(info.context.user)
        if kwargs.get("owner"):
            links = CollectionUserLink.objects.filter(
                user__name__icontains=kwargs["owner"], permission=4
            )
            collections = collections.filter(collectionuserlink__in=links)
        if kwargs.get("created"):
            timestamp = time.time() - {
                "day": 86400, "week": 604800, "month": 2592000, "6month": 15768000, "year": 31557600
            }.get(kwargs["created"], 0)
            collections = collections.filter(created__gte=timestamp)
        if kwargs.get("sort"): collections = collections.order_by(kwargs["sort"])
        return collections
    

    def resolve_search_samples(self, info, **kwargs):
        samples = Sample.objects.filter(
            name__icontains=kwargs["query"].lower()
        ).viewable_by(info.context.user)
        if kwargs.get("organism"):
            samples = samples.filter(organism__icontains=kwargs["organism"])
        if kwargs.get("owner"):
            links = CollectionUserLink.objects.filter(
                user__name__icontains=kwargs["owner"], permission=4
            )
            samples = samples.filter(collection__collectionuserlink__in=links)
        if kwargs.get("created"):
            timestamp = time.time() - {
                "day": 86400, "week": 604800, "month": 2592000, "6month": 15768000, "year": 31557600
            }.get(kwargs["created"], 0)
            samples = samples.filter(created__gte=timestamp)
        if kwargs.get("sort"): samples = samples.order_by(kwargs["sort"])
        return samples
    

    def resolve_search_executions(self, info, **kwargs):
        executions = Execution.objects.filter(
            name__icontains=kwargs["query"].lower()
        ).select_related("command").prefetch_related("users").viewable_by(info.context.user)
        if kwargs.get("command"):
            executions = executions.filter(command__name__icontains=kwargs["command"])
        if kwargs.get("owner"):
            links = ExecutionUserLink.objects.filter(
                user__name__icontains=kwargs["owner"], permission=4
            )
            executions = executions.filter(executionuserlink__in=links)
        if kwargs.get("created"):
            timestamp = time.time() - {
                "day": 86400, "week": 604800, "month": 2592000, "6month": 15768000, "year": 31557600
            }.get(kwargs["created"], 0)
            executions = executions.filter(created__gte=timestamp)
        if kwargs.get("sort"): executions = executions.order_by(kwargs["sort"])
        return executions




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
    process_group_invitation = ProcessGroupInvitationMutation.Field()
    make_group_admin = MakeGroupAdminMutation.Field()
    revoke_group_admin = RevokeGroupAdminMutation.Field()
    remove_user_from_group = RemoveUserFromGroup.Field()
    leave_group = LeaveGroup.Field()

    create_collection = CreateCollectionMutation.Field()
    update_collection = UpdateCollectionMutation.Field()
    update_collection_access = UpdateCollectionAccessMutation.Field()
    delete_collection = DeleteCollectionMutation.Field()

    update_sample = UpdateSampleMutation.Field()
    update_sample_access = UpdateSampleAccessMutation.Field()
    delete_sample = DeleteSampleMutation.Field()

    update_execution = UpdateExecutionMutation.Field()
    update_execution_access = UpdateExecutionAccessMutation.Field()
    delete_execution = DeleteExecutionMutation.Field()

schema = graphene.Schema(query=Query, mutation=Mutation)