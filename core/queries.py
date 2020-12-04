import graphene
from graphene_django.types import DjangoObjectType
from .models import *

class UserType(DjangoObjectType):
    
    class Meta:
        model = User
        exclude_fields = ["password"]
    
    id = graphene.ID()
    groups = graphene.List("core.queries.GroupType")
    admin_groups = graphene.List("core.queries.GroupType")
    invitations = graphene.List("core.queries.GroupInvitationType")

    def resolve_groups(self, info, **kwargs):
        return self.groups.all()
    

    def resolve_admin_groups(self, info, **kwargs):
        return self.admin_groups.all()
    

    def resolve_invitations(self, info, **kwargs):
        return self.group_invitations.all()



class GroupType(DjangoObjectType):
    
    class Meta:
        model = Group
    
    id = graphene.ID()
    user_count = graphene.Int()
    users = graphene.List("core.queries.UserType")
    admins = graphene.List("core.queries.UserType")
    invitations = graphene.List("core.queries.GroupInvitationType")

    def resolve_user_count(self, info, **kwargs):
        return self.users.count()
        

    def resolve_users(self, info, **kwargs):
        return self.users.all()
    

    def resolve_admins(self, info, **kwargs):
        return self.admins.all()
    

    def resolve_invitations(self, info, **kwargs):
        return self.group_invitations.all()




class GroupInvitationType(DjangoObjectType):
    
    class Meta:
        model = GroupInvitation
    
    id = graphene.ID()