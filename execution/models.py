import os
import json
import time
import shutil
import glob
import traceback
import re
import subprocess
from django_random_id_model import RandomIDModel
from django.db import models
from django.conf import settings
from samples.models import Collection, Sample
from core.models import User

class Command(RandomIDModel):
    """Some analysis tool that can be run, usually linked to a Nextflow
    script."""

    class Meta:
        db_table = "commands"
    
    name = models.CharField(max_length=100)
    description = models.TextField()
    nextflow = models.CharField(blank=True, null=True, max_length=200)
    category = models.CharField(max_length=200)
    output_type = models.CharField(max_length=200)
    post_task = models.CharField(max_length=100, blank=True, null=True)
    can_create_sample = models.BooleanField(default=False)

    def __str__(self):
        return self.name
    
    @property
    def input_schema(self):
        try:
            with open(os.path.join(settings.NF_ROOT, self.nextflow, "schema.json")) as f:
                return json.dumps(json.load(f)["inputs"])
        except FileNotFoundError:
            return None
    

    @property
    def output_schema(self):
        with open(os.path.join(settings.NF_ROOT, self.nextflow, "schema.json")) as f:
            return json.load(f)["outputs"]



class Execution(RandomIDModel):

    class Meta:
        db_table = "executions"
        ordering = ["created"]
    
    name = models.CharField(max_length=250)
    created = models.IntegerField(default=time.time)
    last_modified = models.IntegerField(default=time.time)


    started = models.IntegerField(blank=True, null=True)
    finished = models.IntegerField(blank=True, null=True)
    
    status = models.CharField(max_length=50, blank=True, null=True)
    warning = models.TextField(blank=True, null=True)
    error = models.TextField(blank=True, null=True)

    nf_terminal = models.TextField(blank=True, null=True)
    nf_id = models.CharField(max_length=100, blank=True, null=True)

    input = models.TextField(default="{}")
    output = models.TextField(default="{}")

    command = models.ForeignKey(Command, null=True, on_delete=models.SET_NULL, related_name="executions")
    demultiplex_execution = models.ForeignKey("execution.Execution", null=True, blank=True, on_delete=models.SET_NULL, related_name="demultiplexed")
    downstream = models.ManyToManyField("execution.Execution", related_name="upstream")
    parent = models.ForeignKey("execution.Execution", null=True, blank=True, on_delete=models.SET_NULL, related_name="children")

    private = models.BooleanField(default=True)

    sample = models.ForeignKey(Sample, blank=True, null=True, on_delete=models.SET_NULL, related_name="executions")
    collection = models.ForeignKey(Collection, blank=True, null=True, on_delete=models.SET_NULL, related_name="executions")
    initiator = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL, related_name="initiated_executions")
    users = models.ManyToManyField(User, through="execution.ExecutionUserLink", related_name="executions")

    def __str__(self):
        return self.name
    

    def save(self, *args, update_last_modified=True, **kwargs):
        """If the model is being updated, change the last_modified time."""
        
        if self._state.adding is False and update_last_modified:
            self.last_modified = int(time.time())
        super(Execution, self).save(*args, **kwargs)
    

    def start_now(self):
        """Sets the execution's 'started' property to the current time."""

        self.started = time.time()
        self.save()
    

    def finish_now(self):
        """Sets the execution's 'finished' property to the current time."""

        self.finished = time.time()
        self.save()
    

    def prepare_directory(self, uploads):
        """Creates a directory for the execution in the correct place. It also
        takes a list of uploaded files and saves them to the new directory.
        Finally, the Nextflow script needed to run it is copied over."""

        os.mkdir(os.path.join(settings.DATA_ROOT, str(self.id)))    
        for upload in uploads:
            with open(os.path.join(settings.DATA_ROOT, str(self.id), upload.name), "wb+") as f:
                for chunk in upload.chunks():
                    f.write(chunk)
        shutil.copy(
            os.path.join(settings.NF_ROOT, self.command.nextflow, f"{self.command.nextflow}.nf"),
            os.path.join(settings.DATA_ROOT, str(self.id), "run.nf"),
        )
    

    def run(self):
        """Runs the relevant Nextflow script. Params are passed in from the
        inputs the user supplied when the execution object was created. This
        method expects the execution directory to already exist and for any
        uploaded files to be in the directory, but otherwise it handles
        everything about the running of the command."""

        try:
            run = lambda command: subprocess.run(
                command,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True,
                cwd=os.path.join(settings.DATA_ROOT, str(self.id)), shell=True
            )
            self.attach_to_upstream()
            output = run(self.generate_command())
            self.nf_terminal = output.stdout
            self.nf_id = re.search(r"\[(\w+_\w+)\]", output.stdout)[1]
            output = run(f"nextflow log {self.nf_id} -f process,workdir,status")
            processes = [l.split("\t") for l in output.stdout.strip().splitlines()]
            for process in processes:
                self.add_process_from_log(process)
            self.collect_outputs_from_directory()
            self.status = "OK"
            self.save()
        except Exception as e:
            self.status = "ER"
            self.nf_terminal = traceback.format_exc()
            self.error = str(e)
            self.save()
    

    def attach_to_upstream(self):
        for input in json.loads(self.input):
            if input["type"] == "data":
                execution = Execution.objects.get(id=input["value"])
                execution.downstream.add(self)
                if not self.sample and execution.sample:
                    self.sample = execution.sample
                if not self.collection and execution.collection:
                    self.collection = execution.collection
                self.save()
                execution.save()
    

    def generate_command(self):
        """Gets the bash command to run the nextflow script."""

        params = []
        for input in json.loads(self.input):
            if input["type"] == "file":
                quote = '"' if " " in input["value"]["file"] else ""
                params.append(f"--{input['name']} {quote}{input['value']['file']}{quote}")
            if input["type"] == "data":
                execution = Execution.objects.get(id=input["value"])
                outputs = json.loads(execution.output)
                files = [o for o in outputs if "file" in o["type"]]
                if len(files):
                    value = files[0]["value"][0] if isinstance(files[0]["value"], list) else files[0]["value"]
                    filename = value["file"]
                    location = os.path.join(settings.DATA_ROOT, str(input["value"]), filename)
                    quote = '"' if " " in location else ""
                    params.append(f"--{input['name']} {quote}{location}{quote}")
        params = " ".join(params)
        config = os.path.join(settings.NF_ROOT, self.command.nextflow, "nextflow.config")
        return f"nextflow -C {config} run run.nf {params}"


    def add_process_from_log(self, process):
        """Creates a child Nextflow Process from the description of it in the
        log command."""

        with open(os.path.join(process[1], ".command.out")) as f:
            stdout = f.read()
        with open(os.path.join(process[1], ".command.err")) as f:
            stderr = f.read()
        if process[2] == "-" and not self.status:
            self.status = "ER"
            self.error = f"Nextflow process {process[0]} failed"
        NextflowProcess.objects.create(
            name=process[0],
            workdir=process[1],
            status=process[2],
            stdout=stdout,
            stderr=stderr,
            execution=self
        )


    def collect_outputs_from_directory(self):
        """Populates the execution object's `output` field after it has run, by
        looking at any files produced and any values printed during the run."""

        outputs = []
        schema = self.command.output_schema
        directory = os.path.join(settings.DATA_ROOT, str(self.id))
        for output in schema:
            if output["type"] == "file":
                matches = glob.glob(os.path.join(directory, output["match"]))
                if matches:
                    outputs.append({
                        "name": output["name"], "type": "file",
                        "value": [{
                            "file": match.split(os.path.sep)[-1],
                            "size": os.path.getsize(os.path.join(directory, match))
                        } for match in matches]
                    })
            if output["type"] == "basic":
                for process in self.nextflow_processes.all():
                    for line in process.stdout.splitlines():
                        if line.startswith(output["match"]):
                            outputs.append({
                                "name": output["name"], "type": "basic",
                                "value": line[len(output["match"]):].strip()
                            })
                            break
        self.output = json.dumps(outputs)
        self.save()



class NextflowProcess(RandomIDModel):
    """The execution of some nextflow process within a nextflow script."""

    name = models.CharField(max_length=200)
    status = models.CharField(max_length=40)
    workdir = models.CharField(max_length=200)
    stdout = models.TextField()
    stderr = models.TextField()
    execution = models.ForeignKey(Execution, on_delete=models.CASCADE, related_name="nextflow_processes")
    
    def __str__(self):
        return self.name



class ExecutionUserLink(models.Model):
    """Describes the nature of the relationship between a user and execution."""

    class Meta:
        db_table = "execution_user_links"
    
    PERMISSIONS = [[1, "access"], [2, "edit"], [3, "share"], [4, "own"]]

    execution = models.ForeignKey(Execution, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    permission = models.IntegerField(choices=PERMISSIONS, default=1)