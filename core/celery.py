import os
import json
import glob
import subprocess
import shutil
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
    returncode = 0
    try:
        from subprocess import PIPE, run
        params = []
        for input in json.loads(execution.input):
            if input["type"] == "file":
                params.append(f"--{input['name']} {input['value']['file']}")
        params = " ".join(params)
        config = os.path.join(settings.NF_ROOT, execution.command.nextflow, "nextflow.config")
        result = run(f"nextflow -C {config} run run.nf {params}".split(), stdout=PIPE, stderr=PIPE, universal_newlines=True, cwd=os.path.join(
            settings.DATA_ROOT, str(execution_id)
        ))

        if result.returncode == 1:
            returncode = 1
            directory = os.path.join(settings.DATA_ROOT, str(execution.id), "work")
            dirs = os.listdir(directory)
            if dirs: directory = os.path.join(directory, dirs[0])
            dirs = os.listdir(directory)
            if dirs: directory = os.path.join(directory, dirs[0])
            if "output.txt" in os.listdir(directory):
                shutil.copy(
                    os.path.join(directory, "output.txt"),
                    os.path.join(settings.DATA_ROOT, str(execution.id), "output.txt")
                )
            execution.status = "ER"
            execution.error = "The nextflow job failed to run (see terminal)"

        

        outputs = []
        with open(os.path.join(settings.NF_ROOT, execution.command.nextflow, "schema.json")) as f:
            output_schema = json.load(f)["outputs"]

        try:
            with open(os.path.join(settings.DATA_ROOT, str(execution.id), "output.txt")) as f:
                terminal_output = f.read().splitlines()
        except FileNotFoundError:
            terminal_output = []

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
            if output["type"] == "basic":
                for line in terminal_output:
                    if line.startswith(output["match"]):
                        outputs.append({
                            "name": output["name"],
                            "type": "basic",
                            "value": line[len(output["match"]):].strip()
                        })
                        terminal_output.remove(line)
                        break
        execution.output = json.dumps(outputs)
        with open(os.path.join(settings.DATA_ROOT, str(execution.id), "output.txt"), "w") as f:
            f.write("\n".join(terminal_output))
        
    except Exception as e:
        execution.error = str(e)
        execution.status = "ER"
    finally:
        execution.finished = time.time()
        execution.save()
    return returncode

