from django.db import transaction
from django.forms import ModelForm, BooleanField
from analysis.models import Collection, Paper, Sample, Data

class CollectionForm(ModelForm):
    """Creates or edits a collection."""

    class Meta:
        model = Collection
        exclude = ["id", "users", "groups", "created", "modified"]
    
    def save(self, *args, **kwargs):
        with transaction.atomic():
            for sample in self.instance.samples.all():
                sample.private = self.instance.private
                for job in sample.jobs.all():
                    job.private = self.instance.private
                    job.save()
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
        exclude = ["id", "created", "modified", "qc_message", "qc_pass", "users", "collection", "initiator"]
    

    def clean_private(self):
        if self.instance.collection: return self.instance.collection.private
        return self.data.get("private", self.instance.private)
    

    def save(self, *args, **kwargs):
        with transaction.atomic():
            for job in self.instance.jobs.all():
                job.private = self.instance.private
                job.save()
        return super().save(self, *args, **kwargs)



class DataForm(ModelForm):

    class Meta:
        model = Data
        fields = ["private"]
    
    private = BooleanField(required=True)
    

    '''def clean_private(self):
        #if self.instance.collection: return self.instance.collection.private
        print(self.data)
        return self.data.get("private", self.instance.link.private)'''
    

    def save(self, *args, **kwargs):
        return super().save(self, *args, **kwargs)