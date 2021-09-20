from core.permissions import can_user_edit_execution, can_user_share_execution, execution_owners, is_user_owner_of_execution
import graphene
from .models import Command, Execution, NextflowProcess
from graphene_django import DjangoObjectType

class CommandType(DjangoObjectType):
    
    class Meta:
        model = Command
    
    id = graphene.ID()

    input_schema = graphene.String()



class ExecutionType(DjangoObjectType):
    
    class Meta:
        model = Execution
    
    id = graphene.ID()
    owners = graphene.List("core.queries.UserType")
    is_owner = graphene.Boolean()
    can_share = graphene.Boolean()
    can_edit = graphene.Boolean()

    def resolve_owners(self, info, **kwargs):
        return execution_owners(self)

    def resolve_is_owner(self, info, **kwargs):
        return is_user_owner_of_execution(info.context.user, self)
    
    def resolve_can_share(self, info, **kwargs):
        return can_user_share_execution(info.context.user, self)
    
    def resolve_can_edit(self, info, **kwargs):
        return can_user_edit_execution(info.context.user, self)



class NextflowProcessType(DjangoObjectType):
    
    class Meta:
        model = NextflowProcess
    
    id = graphene.ID()