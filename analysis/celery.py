
import os
import time
import pandas as pd
import json
import shutil
from celery import Celery
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
        job.execution = execution
    finally:
        job.finished = time.time()
        job.save()



def assign_job_parents(job, execution):
    upstream_samples = [
        data.upstream_process_execution.execution.job.sample for data in
        execution.upstream_data.exclude(upstream_process_execution=None)
    ]
    sample_ids = set([s.id for s in upstream_samples if s])
    if len(sample_ids) == 1:
        job.sample_id = sample_ids[0]
        job.save()
    else:
        upstream_collections = [
            data.upstream_process_execution.execution.job.collection for data in
            execution.upstream_data.exclude(upstream_process_execution=None)
        ] + [
            data.upstream_process_execution.execution.job.sample.collection for data in
            execution.upstream_data.exclude(upstream_process_execution=None) if
            data.upstream_process_execution.execution.job.sample
        ]
        collection_ids = set([c.id for c in upstream_collections if c])
        if len(collection_ids) == 1:
            job.collection_id = collection_ids[0]
            job.save()
