
import collections
import os
import re
import time
import pandas as pd
import json
import shutil
import importlib
from celery import Celery
from zipfile import ZipFile
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
app = Celery("execution")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

@app.task(name="run_pipeline")
def run_pipeline(kwargs, job_id, user_id):
    """Runs a pipeline in celery. An iMaps Job object should already have been
    created, and this will create the accompanying django_nextflow Execution
    object.
    
    Takes the original mutation kwargs, the job_id, and the user_id of the user
    who submitted the mutation.
    
    Once execution is complete, links to existing samples and collections will
    be created, DataLink objects for every Data object will be created, any
    Samples that need to be created will be created, and any Sample metadata
    that needs to be created will be updated."""

    from django_nextflow.models import Pipeline
    from analysis.models import Job

    job = Job.objects.filter(id=job_id).first()
    job.started = time.time()
    job.save()
    pipeline = Pipeline.objects.filter(id=kwargs["pipeline"]).first()
    try:
        execution = pipeline.run(
            params=json.loads(kwargs["inputs"]),
            data_params=json.loads(kwargs["dataInputs"]),
            profile=["iMaps"]
        )
        assign_job_parents(job, execution)
        create_data_links(execution)
        create_samples(execution, user_id)
        
        for process_execution in execution.process_executions.all():
            if process_execution.process_name.split(":")[-1] in settings.PROCESS_FUNCTIONS:
                for funcname in settings.PROCESS_FUNCTIONS[process_execution.process_name.split(":")[-1]]:
                    module = ".".join(funcname.split(".")[:-1])
                    func = getattr(importlib.import_module(module), funcname.split(".")[-1])
                    func(process_execution)
        job.execution = execution
    finally:
        job.finished = time.time()
        job.save()



def assign_job_parents(job, execution):
    """Jobs belong to a sample if all their inputs are from a single sample (or
    no sample), and likewise for collections. This function looks at the inputs
    to a job and assigns these parents."""

    from analysis.models import Sample

    upstream_samples = []
    for data in execution.upstream_data.all():
        if data.upstream_process_execution:
            upstream_samples.append(
                data.upstream_process_execution.execution.job.sample
            )
        upstream_samples.append(Sample.objects.filter(reads=data).first())
    sample_ids = set([s.id for s in upstream_samples if s])
    if len(sample_ids) == 1:
        job.sample_id = list(sample_ids)[0]
        job.save()
    else:
        upstream_collections = []
        for data in execution.upstream_data.all():
            if data.upstream_process_execution:
                upstream_collections.append(
                    data.upstream_process_execution.execution.job.collection
                ) 
                if data.upstream_process_execution.execution.job.sample:
                    upstream_collections.append(
                        data.upstream_process_execution.execution.job.sample.collection
                    ) 
            upstream_collections.append(data.link.collection)
        collection_ids = set([c.id for c in upstream_collections if c])
        if len(collection_ids) == 1:
            job.collection_id = list(collection_ids)[0]
            job.save()


def create_data_links(execution):
    """An execution will create various new Data objects, but they also need
    iMaps DataLink objects accompanying them. This function creates those."""

    from django_nextflow.models import Data
    from analysis.models import DataLink
    for data in Data.objects.filter(upstream_process_execution__execution=execution):
        DataLink.objects.create(data=data)


def create_samples(execution, user_id):
    """If an execution involved demultiplexing, samples need to be created for
    the reads files produced."""

    from django_nextflow.models import Data
    from analysis.models import Sample, SampleUserLink
    from analysis.models import Collection, CollectionUserLink
    from core.models import User
    from genomes.models import Gene
    from core.permissions import does_user_have_permission_on_collection

    
    for process_name in settings.READS_GENERATING_PROCESSES:
        # Were any data files created by processes of this name?
        for data in Data.objects.filter(
            upstream_process_execution__execution=execution,
            upstream_process_execution__process_name=process_name,
            filetype__in=settings.READS_EXTENSIONS
        ).exclude(filename__endswith="no_match.fastq.gz"):
            # Got a reads file that should have a sample
            sample_name = data.filename
            for extension in settings.READS_EXTENSIONS:
                if sample_name.endswith(extension):
                    sample_name = sample_name[:-len(extension) - 1]
            if sample_name.startswith("ultraplex_demux_"):
                sample_name = sample_name[16:]
            sample = Sample.objects.create(name=sample_name, reads=data)
            SampleUserLink.objects.create(sample=sample, user_id=user_id, permission=3)

            # Annotate it with meta information
            sheet = execution.upstream_data.filter(link__is_annotation=True).first()
            if not sheet: continue
            df = pd.read_csv(sheet.full_path)
            for index, row in df.iterrows():
                if row["Sample Name"] == sample_name:
                    meta = {key.replace(" (optional)", ""): None if pd.isna(value) else value for key, value in dict(row).items()}
                    sample.meta = json.dumps(meta)
                    sample.organism = meta.get("Species")
                    sample.method = meta.get("Method")
                    sample.source = meta.get("Cell or Tissue")
                    gene = meta.get("Protein")
                    sample.gene = Gene.objects.filter(name=gene, species=meta.get("Species")).first()
                    sample.scientist = User.objects.filter(username=meta.get("Scientist")).first()
                    sample.pi = User.objects.filter(username=meta.get("PI")).first()
                    collection = Collection.objects.filter(name=meta["Collection Name"]).first()
                    if not collection and sample.scientist:
                        sample.collection = Collection.objects.create(
                            name=meta["Collection Name"],
                            description=meta["Collection Name"]
                        )
                        CollectionUserLink.objects.create(
                            collection=sample.collection,
                            user=sample.scientist, permission=4
                        )
                    elif does_user_have_permission_on_collection(User.objects.get(id=user_id), collection, 2):
                        sample.collection = collection
                    sample.save()

                
def annotate_samples_from_fastqc(process_execution):

    # Is there a sample associated?
    data_input = process_execution.upstream_data.first()
    if not data_input or not data_input.sample: return
    sample = data_input.sample

    zip = process_execution.downstream_data.filter(filetype="zip").first()
    if zip:
        contents = ZipFile(zip.full_path)
        for name in contents.namelist():
            if name.endswith("summary.txt"):
                sample.qc_pass = contents.read(name).startswith(b"PASS")
    sample.save()
