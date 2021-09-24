import time
from django_random_id_model import RandomIDModel
from django.db import models
from core.models import User, Group

class Collection(RandomIDModel):
    """A collection of samples that belong together in some sense, either as
    part of a single paper or to answer a single research question.
    
    It is either private or not, which determies whether the public can view
    it."""

    class Meta:
        db_table = "collections"
        ordering = ["-created"]

    name = models.CharField(max_length=200)
    created = models.IntegerField(default=time.time)
    last_modified = models.IntegerField(default=time.time)
    description = models.TextField(default="", blank=True)
    private = models.BooleanField(default=True)
    users = models.ManyToManyField(User, through="samples.CollectionUserLink", related_name="collections")
    groups = models.ManyToManyField(Group, through="samples.CollectionGroupLink", related_name="collections")

    def __str__(self):
        return self.name
    
    def save(self, *args, update_last_modified=True, **kwargs):
        """If the model is being updated, change the last_modified time."""
        
        if self._state.adding is False and update_last_modified:
            self.last_modified = int(time.time())
        super(Collection, self).save(*args, **kwargs)



class Sample(RandomIDModel):
    """A single CLIP experiment."""

    class Meta:
        db_table = "samples"
        ordering = ["-created"]
    
    name = models.CharField(max_length=250)
    created = models.IntegerField(default=time.time)
    last_modified = models.IntegerField(default=time.time)
    private = models.BooleanField(default=True)
    source = models.CharField(max_length=100)
    organism = models.CharField(max_length=100)
    qc_pass = models.BooleanField(null=True)
    qc_message = models.CharField(max_length=100)
    pi_name = models.CharField(max_length=100)
    annotator_name = models.CharField(max_length=100)
    collection = models.ForeignKey(Collection, null=True, on_delete=models.CASCADE, related_name="samples")
    users = models.ManyToManyField(User, through="samples.SampleUserLink", related_name="samples")

    def __str__(self):
        return self.name


    def save(self, *args, update_last_modified=True, **kwargs):
        """If the model is being updated, change the last_modified time."""
        
        if self._state.adding is False and update_last_modified:
            self.last_modified = int(time.time())
        super(Sample, self).save(*args, **kwargs)



class Paper(RandomIDModel):
    """A paper that used data from some iMaps collections."""

    class Meta:
        db_table = "papers"
        ordering = ["year"]

    title = models.CharField(max_length=250)
    url = models.URLField(max_length=200, blank=True, null=True)
    year = models.IntegerField()
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE, related_name="papers")



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