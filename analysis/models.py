import time
from django_random_id_model import RandomIDModel
from django.db import models
from core.models import User, Group
from django_nextflow.models import Execution, Pipeline, Data

class Collection(models.Model):
    """A collection of samples that belong together in some sense, either as
    part of a single paper or to answer a single research question.
    
    It is either private or not, which determies whether the public can view
    it."""

    class Meta:
        db_table = "collections"
        ordering = ["-created"]

    name = models.CharField(max_length=150, unique=True)
    created = models.IntegerField(default=time.time)
    last_modified = models.IntegerField(default=time.time)
    description = models.TextField(default="", blank=True)
    private = models.BooleanField(default=True)
    users = models.ManyToManyField(User, through="analysis.CollectionUserLink", related_name="collections")
    groups = models.ManyToManyField(Group, through="analysis.CollectionGroupLink", related_name="collections")

    def __str__(self):
        return self.name
    
    def save(self, *args, update_last_modified=True, **kwargs):
        """If the model is being updated, change the last_modified time."""
        
        if self._state.adding is False and update_last_modified:
            self.last_modified = int(time.time())
        super(Collection, self).save(*args, **kwargs)
    

    @property
    def all_executions(self):
        return Execution.objects.filter(job__collection=self)
    

    @property
    def all_data(self):
        return (Data.objects.filter(
            upstream_process_execution__execution__job__sample__collection=self
        ) | Data.objects.filter(
            upstream_process_execution__execution__job__collection=self
        ) | Data.objects.filter(
            link__collection=self
        )).distinct()



class Sample(models.Model):
    """A single CLIP experiment."""

    class Meta:
        db_table = "samples"
        ordering = ["-created"]
    
    name = models.CharField(max_length=250)
    created = models.IntegerField(default=time.time)
    modified = models.IntegerField(default=time.time)
    private = models.BooleanField(default=True)
    source = models.CharField(max_length=100)
    organism = models.CharField(max_length=100)
    qc_pass = models.BooleanField(null=True)
    qc_message = models.CharField(max_length=100)
    pi_name = models.CharField(max_length=100)
    annotator_name = models.CharField(max_length=100)
    initiator = models.ForeignKey(Data, null=True, on_delete=models.SET_NULL, related_name="samples")
    collection = models.ForeignKey(Collection, null=True, on_delete=models.CASCADE, related_name="samples")
    users = models.ManyToManyField(User, through="analysis.SampleUserLink", related_name="samples")

    def __str__(self):
        return self.name


    def save(self, *args, update_last_modified=True, **kwargs):
        """If the model is being updated, change the last_modified time."""
        
        if self._state.adding is False and update_last_modified:
            self.last_modified = int(time.time())
        super(Sample, self).save(*args, **kwargs)
    

    @property
    def all_data(self):
        return Data.objects.filter(upstream_process_execution__execution__job__sample=self)



class Paper(RandomIDModel):
    """A paper that used data from some iMaps collections."""

    class Meta:
        db_table = "papers"
        ordering = ["year"]

    title = models.CharField(max_length=250)
    url = models.URLField(max_length=200, blank=True, null=True)
    year = models.IntegerField()
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE, related_name="papers")



class Job(models.Model):

    class Meta:
        db_table = "jobs"
        ordering = ["created"]

    created = models.IntegerField(default=time.time)
    modified = models.IntegerField(default=time.time)
    started = models.IntegerField(null=True)
    finished = models.IntegerField(null=True)
    pipeline = models.ForeignKey(Pipeline, null=True, on_delete=models.SET_NULL, related_name="jobs")
    private = models.BooleanField(default=True)
    params = models.TextField(default="{}")
    data_params = models.TextField(default="{}")
    execution = models.OneToOneField(Execution, null=True, on_delete=models.SET_NULL, related_name="job")
    sample = models.ForeignKey(Sample, null=True, on_delete=models.SET_NULL, related_name="jobs")
    collection = models.ForeignKey(Collection, null=True, on_delete=models.SET_NULL, related_name="jobs")
    users = models.ManyToManyField(User, through="analysis.JobUserLink", related_name="jobs")



class CollectionUserLink(models.Model):
    """Describes the nature of the relationship between a user and
    collection."""

    class Meta:
        db_table = "collection_user_links"
    
    PERMISSIONS = [[1, "access"], [2, "edit"], [3, "share"], [4, "own"]]

    collection = models.ForeignKey(Collection, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    permission = models.IntegerField(choices=PERMISSIONS, default=1)



class CollectionGroupLink(models.Model):
    """Describes the nature of the relationship between a group and
    collection."""

    class Meta:
        db_table = "collection_group_links"
    
    PERMISSIONS = [[1, "access"], [2, "edit"], [3, "share"]]

    collection = models.ForeignKey(Collection, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    permission = models.IntegerField(choices=PERMISSIONS, default=1)



class SampleUserLink(models.Model):
    """Describes the nature of the relationship between a user and sample."""

    class Meta:
        db_table = "sample_user_links"
    
    PERMISSIONS = [[1, "access"], [2, "edit"], [3, "share"]]

    sample = models.ForeignKey(Sample, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    permission = models.IntegerField(choices=PERMISSIONS, default=1)



class JobUserLink(models.Model):
    """Describes the nature of the relationship between a user and job."""

    class Meta:
        db_table = "job_user_links"
    
    PERMISSIONS = [[1, "access"], [2, "edit"], [3, "share"]]

    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    permission = models.IntegerField(choices=PERMISSIONS, default=1)



class DataLink(models.Model):

    class Meta:
        db_table = "data_links"

    data = models.OneToOneField(Data, on_delete=models.CASCADE, related_name="link")
    private = models.BooleanField(default=True)
    collection = models.ForeignKey(Collection, null=True, on_delete=models.SET_NULL)



class DataUserLink(models.Model):
    """Describes the nature of the relationship between a user and data file."""

    class Meta:
        db_table = "data_user_links"
    
    PERMISSIONS = [[1, "access"], [2, "edit"], [3, "share"]]

    data = models.ForeignKey(Data, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    permission = models.IntegerField(choices=PERMISSIONS, default=1)