import os
import json
import glob
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
        time.sleep(2)
        outputs = []
        with open(os.path.join(settings.NF_ROOT, execution.command.nextflow, "schema.json")) as f:
            output_schema = json.load(f)["outputs"]
        for output in output_schema:
            if output["type"] == "file":
                matches = glob.glob(os.path.join(settings.DATA_ROOT, str(execution_id), output["match"]))
                if matches:
                    outputs.append({
                        "name": output["name"],
                        "type": "file",
                        "value": [{
                            "file": match.split(os.path.sep)[-1],
                            "size": os.path.getsize(os.path.join(settings.DATA_ROOT, str(execution_id), match))
                        } for match in matches]
                    })
        execution.output = json.dumps(outputs)
        
    except Exception as e:
        execution.error = str(e)
        execution.status = "ER"
    finally:
        execution.finished = time.time()
        execution.save()
    return 0

