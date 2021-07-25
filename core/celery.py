import os
from celery import Celery

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
    try:
        result = execution.run()
        if result.returncode == 1:
            execution.fetch_terminal_from_workdir()
            execution.status = "ER"
            execution.error = "The nextflow job failed to run (see terminal)"
        execution.collect_outputs_from_directory()        
    except Exception as e:
        execution.error = str(e)
        execution.status = "ER"
    finally:
        execution.finish_now()

