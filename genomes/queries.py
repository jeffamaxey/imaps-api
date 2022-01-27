import graphene
from graphene_django import DjangoObjectType
from genomes.models import Gene, Species

class SpeciesType(DjangoObjectType):
    
    class Meta:
        model = Species
    
    id = graphene.ID()



class GeneType(DjangoObjectType):
    
    class Meta:
        model = Gene
    
    id = graphene.ID()