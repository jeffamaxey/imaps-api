import graphene
from graphene_django import DjangoObjectType
from genomes.models import Gene

class GeneType(DjangoObjectType):
    
    class Meta:
        model = Gene
    
    id = graphene.ID()