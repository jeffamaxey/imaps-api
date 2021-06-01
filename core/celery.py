import os
from django.conf import settings
from subprocess import Popen, PIPE
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

app = Celery("core")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()


@app.task(name="run_command")
def run_command(execution_id, inputs, requirements):
    command = f"docker run -v {os.path.join(settings.DATA_ROOT, str(execution_id))}:/job/ {requirements['executor']['docker']['image']}"
    p = Popen(command.split(), stdin=PIPE, stdout=PIPE, stderr=PIPE)
    output, err = p.communicate()
    return 0

