from django.forms import ModelForm
from execution.models import Execution

class ExecutionForm(ModelForm):
    """Edits an execution."""

    class Meta:
        model = Execution
        fields = ["name", "private"]
    
    def clean_private(self):
        if self.instance.collection: return self.instance.collection.private
        if self.instance.sample: return self.instance.sample.private
        return self.data.get("private", self.instance.private)