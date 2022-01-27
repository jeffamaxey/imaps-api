import requests
from tqdm import tqdm
from django.core.management.base import BaseCommand
from genomes.models import Gene, Species
from django.db import transaction
from genomes.data import SPECIES

class Command(BaseCommand):
    help = "Updates genes from ENSEMBL"

    def handle(self, *args, **options):
        url =  "http://www.ensembl.org/biomart/martservice?query="
        query = """
        <?xml version="1.0" encoding="UTF-8"?>
        <!DOCTYPE Query>
        <Query  virtualSchemaName="default" formatter="TSV" header="0" uniqueRows="0" count="" datasetConfigVersion="0.6">
            <Dataset name="{}_gene_ensembl" interface="default">
                <Filter name="biotype" value="protein_coding"/>
                <Attribute name="external_gene_name" />
            </Dataset>
        </Query>"""

        
        for species in Species.objects.all():
            self.stdout.write(f"Requesting {species.name} genes...")
            resp = requests.get(url + query.format(species.ensembl_id).strip().replace("\n", ""))
            if resp.status_code != 200: continue
            genes = resp.text.splitlines()
            self.stdout.write(f"There are {len(genes)} of them")
            with transaction.atomic():
                deleted = Gene.objects.filter(species=species).exclude(name__in=genes).delete()[0]
                if deleted:
                    self.stdout.write(f"Deleted {deleted} genes which are no longer present")
                for gene in tqdm(genes):
                    Gene.objects.get_or_create(name=gene, species=species)