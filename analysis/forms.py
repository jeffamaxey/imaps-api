from django.db import transaction
from django.forms import ModelForm
from analysis.models import Collection, Paper, Sample

class CollectionForm(ModelForm):
    """Creates or edits a collection."""

    class Meta:
        model = Collection
        exclude = ["id", "users", "groups", "created", "last_modified"]
    
    def save(self, *args, **kwargs):
        with transaction.atomic():
            for sample in self.instance.samples.all():
                sample.private = self.instance.private
                for execution in sample.executions.all():
                    execution.private = self.instance.private
                    execution.save()
                sample.save()
            '''for execution in self.instance.executions.all():
                execution.private = self.instance.private
                execution.save()'''
        return super().save(self, *args, **kwargs)



class PaperForm(ModelForm):
    """Creates or edits a paper."""

    class Meta:
        model = Paper
        exclude = ["id"]



class SampleForm(ModelForm):
    """Edits a sample."""

    class Meta:
        model = Sample
        exclude = ["id", "created", "last_modified", "qc_message", "qc_pass", "users", "collection"]
    

    def clean_private(self):
        if self.instance.collection: return self.instance.collection.private
        return self.data.get("private", self.instance.private)
    

    def save(self, *args, **kwargs):
        with transaction.atomic():
            for execution in self.instance.executions.all():
                execution.private = self.instance.private
                execution.save()
        return super().save(self, *args, **kwargs)