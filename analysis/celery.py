
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
    """."""

    from django_nextflow.models import Pipeline, Data
    from analysis.models import DataLink, Job, Sample, SampleUserLink

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
        
        for data in Data.objects.filter(upstream_process_execution__execution=execution):
            DataLink.objects.create(data=data)

        for process_name, filetypes in settings.SAMPLE_PROCESS_DATA:
            for data in Data.objects.filter(
                upstream_process_execution__execution=execution,
                upstream_process_execution__process_name=process_name,
                filetype__in=filetypes
            ):
                sample = Sample.objects.create(
                    name=data.filename,
                    initiator=data
                )
                SampleUserLink.objects.create(sample=sample, user_id=user_id, permission=3)
            
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


def annotate_samples_from_ultraplex(process_execution):
    # Try to get the original spreadsheet
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
                    sample.pi_name = row["PI"]
                    sample.annotator_name = row["Scientist"]
                    sample.organism = species.get(row["Species"], row["Species"])
                    sample.source = row["CellOrTissue"]
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
