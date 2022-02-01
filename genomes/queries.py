import graphene
from graphene_django import DjangoObjectType
from genomes.models import Gene, Species
from core.permissions import readable_jobs

class SpeciesType(DjangoObjectType):
    
    class Meta:
        model = Species
    
    id = graphene.ID()
    
    def resolve_jobs(self, info, **kwargs):
        return readable_jobs(self.jobs.all(), info.context.user)



class GeneType(DjangoObjectType):
    
    class Meta:
        model = Gene
    
    id = graphene.ID()