
import os
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
def run_pipeline(kwargs, job_id):
    """."""

    from django_nextflow.models import Pipeline, Data
    from analysis.models import DataLink, Job

    pipeline = Pipeline.objects.filter(id=kwargs["pipeline"]).first()
    execution = pipeline.run(
        params=json.loads(kwargs["inputs"]),
        data_params=json.loads(kwargs["dataInputs"]),
    )
    for data in Data.objects.filter(upstream_process_execution__execution=execution):
        DataLink.objects.create(data=data)
    job = Job.objects.filter(id=job_id).first()
    job.execution = execution
    job.save()