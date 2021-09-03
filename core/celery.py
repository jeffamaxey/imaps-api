import os
import pandas as pd
import json
import shutil
from celery import Celery
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
app = Celery("core")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

@app.task(name="run_command")
def run_command(execution_id):
    """Execute and execution. This task takes the ID of an execution which has
    been created in the database, and which has a directory created and
    populated for it, but which has not been run.
    
    The execution will be run using Nextflow. If there Nextflow process fails,
    the appropriate information will be collected. Any files or other data
    produced by the process will be collected and noted in the execution's
    database record."""

    from core.models import Execution
    execution = Execution.objects.get(id=execution_id)
    execution.start_now()
    execution.run()

    post_task = globals().get(execution.command.post_task)
    if post_task: 
        post_task(execution.id)

    execution.finish_now()


def post_demultiplex(execution_id):
    from core.models import Sample, Execution, Command, ExecutionUserLink, SampleUserLink
    demultiplex_execution = Execution.objects.get(id=execution_id)
    annotation_execution = demultiplex_execution.upstream.get(command__output_type="samplelist")
    location = os.path.join(
        settings.DATA_ROOT, str(annotation_execution.id),
        json.loads(annotation_execution.input)[0]["value"]["file"]
    )
    dfs = pd.read_excel(location, sheet_name=None)
    matrix = list(dfs.values())[0].values
    outputs = [f for f in os.listdir(os.path.join(settings.DATA_ROOT, str(execution_id))) if f.endswith("fastq.gz")]
    command = Command.objects.filter(category="internal-import").first()
    for row in matrix:
        barcode = row[11].replace("_0", "").replace(",", "")
        data = {
            "sample": row[0], "collection": row[1],
            "barcode": barcode
        }
        matches = [f for f in outputs if f"{data['barcode']}.fastq.gz" in f]
        if len(matches):
            
            with open(os.path.join(settings.NF_ROOT, command.nextflow, "schema.json")) as f:
                inputs = json.load(f)["inputs"]
            inputs[0]["value"] = {"file": f"{row[0]}.fastq.gz", "size": os.path.getsize(
                os.path.join(settings.DATA_ROOT, str(execution_id), matches[0])
            )}
            sample = Sample.objects.create(
                name=row[0],
                source=row[8],
                organism=row[10],
                qc_pass="",
                qc_message="",
                pi_name=row[4],
                annotator_name=row[3]
            )
            SampleUserLink.objects.create(user=demultiplex_execution.owners.first(), sample=sample, permission=3)
            new = Execution.objects.create(
                name=row[0], command=command,
                input=json.dumps(inputs), output="[]",
                demultiplex_execution=demultiplex_execution,
                sample=sample
            )
            ExecutionUserLink.objects.create(user=demultiplex_execution.owners.first(), execution=new, permission=4)
            os.mkdir(os.path.join(settings.DATA_ROOT, str(new.id)))    
            shutil.move(
                os.path.join(settings.DATA_ROOT, str(demultiplex_execution.id), matches[0]),
                os.path.join(settings.DATA_ROOT, str(new.id), f"{row[0]}.fastq.gz"),
            )
            shutil.copy(
                os.path.join(settings.NF_ROOT, new.command.nextflow, f"{new.command.nextflow}.nf"),
                os.path.join(settings.DATA_ROOT, str(new.id), "run.nf"),
            )
            new.start_now()
            new.run()
            new.finish_now()
            for output in json.loads(new.output):
                if output["name"] == "quality_pass":
                    sample.qc_pass = output["value"] == "true"
                    sample.save()
                    break