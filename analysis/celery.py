
import collections
import os
import re
import time
from typing import Collection
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
            if process_execution.process_name in settings.PROCESS_FUNCTIONS:
                for funcname in settings.PROCESS_FUNCTIONS[process_execution.process_name]:
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

    upstream_samples = []
    for data in execution.upstream_data.all():
        if data.upstream_process_execution:
            upstream_samples.append(
                data.upstream_process_execution.execution.job.sample
            ) 
        upstream_samples.append(data.samples.first())
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
    for process_name in settings.READS_GENERATING_PROCESSES:
        for data in Data.objects.filter(
            upstream_process_execution__execution=execution,
            upstream_process_execution__process_name=process_name,
            filetype__in=settings.READS_EXTENSIONS
        ).exclude(filename__endswith="no_match.fastq.gz"):
            sample = Sample.objects.create(
                name=data.filename,
                initiator=data
            )
            SampleUserLink.objects.create(sample=sample, user=user_id, permission=3)


def annotate_samples_from_ultraplex(process_execution):
    # Try to get the original spreadsheet
    from core.models import User
    from analysis.models import Collection, CollectionUserLink
    df = None
    species = {
        "Hs": "Homo sapiens",
        "Mm": "Mus musculus",
        "Sc": "Saccharomyces cerevisiae",
        "Dr": "Danio rerio",
        "Rn": "Rattus norvegicus",
        "Dm": "Drosophila melanogaster",
        "Ec": "Escherichia coli",
        "Sa": "Staphyloccocus aureus",
    }
    barcodes_csv = process_execution.upstream_data.filter(filetype="csv").first()
    if barcodes_csv and barcodes_csv.upstream_process_execution:
        samples_csv = barcodes_csv.upstream_process_execution.upstream_data.filter(filetype="csv").first()
        if samples_csv:
            df = pd.read_csv(samples_csv.full_path)
    if df is None: return  
    for data in process_execution.downstream_data.all():
        if data.samples.count():
            sample = data.samples.first()
            sample_name = data.filename[:-(len(data.filetype) + 1)]
            for row in df.iloc:
                if len(row["SampleName"]) > 3 and row["SampleName"] in sample_name:
                    collection = Collection.objects.filter(name=row["CollectionName"]).first()
                    if not collection:
                        collection = Collection.objects.create(name=row["CollectionName"])
                        user = User.objects.filter(name=row["Scientist"]).first()
                        if user:
                            CollectionUserLink.objects.create(collection=collection, user=user, permission=4)
                    sample.pi_name = row["PI"]
                    sample.annotator_name = row["Scientist"]
                    sample.organism = species.get(row["Species"], row["Species"])
                    sample.source = row["CellOrTissue"]
                    sample.collection = collection
                    sample.save()
                    break


def annotate_samples_from_fastqc(process_execution):
    # Is there a sample associated?
    data_input = process_execution.upstream_data.first()
    if not data_input or not data_input.samples.count(): return
    sample = data_input.samples.first()

    zip = process_execution.downstream_data.filter(filetype="zip").first()
    if zip:
        contents = ZipFile(zip.full_path)
        for name in contents.namelist():
            if name.endswith("summary.txt"):
                sample.qc_pass = contents.read(name).startswith(b"PASS")
            if name.endswith("fastqc_data.txt"):
                data = contents.read(name).decode()
                message = []
                for query in [
                    "Total Sequences", "Sequences flagged as poor quality",
                    "Sequence length"
                ]:
                    match = re.search(f"{query}[ \\t](.+)", data)
                    if match: message.append(match[0].replace("\t", " "))
                sample.qc_message = "; ".join(message)
    sample.save()
