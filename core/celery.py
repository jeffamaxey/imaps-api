import os
import json
import glob
import subprocess
from django.conf import settings
from subprocess import Popen, PIPE
import time
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

app = Celery("core")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()

@app.task(name="run_command")
def run_command(execution_id):
    from core.models import Execution
    execution = Execution.objects.get(id=execution_id)
    execution.started = time.time()
    execution.save()
    try:
        from subprocess import PIPE, run
        params = []
        for input in json.loads(execution.input):
            if input["type"] == "file":
                params.append(f"--{input['name']} {input['value']['file']}")
        params = " ".join(params)
        print(f"nextflow run run.nf {params}")
        result = run(f"nextflow run run.nf {params}".split(), stdout=PIPE, stderr=PIPE, universal_newlines=True, cwd=os.path.join(
            settings.DATA_ROOT, str(execution_id)
        ))
        
        print(result.returncode, result.stdout, result.stderr)

        outputs = []
        with open(os.path.join(settings.NF_ROOT, execution.command.nextflow, "schema.json")) as f:
            output_schema = json.load(f)["outputs"]
        print(output_schema)
        print(os.listdir(os.path.join(settings.DATA_ROOT, str(execution_id))))
        for output in output_schema:
            if output["type"] == "file":
                print(output)
                matches = glob.glob(os.path.join(settings.DATA_ROOT, str(execution_id), output["match"]))
                print(matches)
                if matches:
                    outputs.append({
                        "name": output["name"],
                        "type": "file",
                        "value": [{
                            "file": match.split(os.path.sep)[-1],
                            "size": os.path.getsize(os.path.join(settings.DATA_ROOT, str(execution_id), match))
                        } for match in matches]
                    })
        print(outputs)
        execution.output = json.dumps(outputs)
        
    except Exception as e:
        execution.error = str(e)
        execution.status = "ER"
    finally:
        execution.finished = time.time()
        execution.save()
    return 0

