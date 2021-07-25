import time
import jwt
import json
import os
import shutil
import glob
import base64
from subprocess import PIPE, run
from random import randint
from django_random_id_model import RandomIDModel
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import make_password

def create_filename(instance, filename):
    """Creates a filename for some uploaded image, from the owning object's ID,
    and class name."""
    
    extension = "." + filename.split(".")[-1] if "." in filename else ""
    hashed_class = base64.b64encode(instance.__class__.__name__.encode())
    return f"{instance.id}{hashed_class}{extension}"


def slug_validator(value):
    """A stricter version of Django's built in slug validation."""

    if len(value) < 2:
        raise ValidationError("This must be at least 2 characters long")

class User(RandomIDModel):
    """The user model."""

    class Meta:
        db_table = "users"
        ordering = ["created"]

    username = models.SlugField(max_length=30, unique=True, validators=[slug_validator])
    email = models.EmailField(max_length=200, unique=True)
    password = models.CharField(max_length=128)
    last_login = models.IntegerField(null=True, default=None)
    created = models.IntegerField(default=time.time)
    name = models.CharField(max_length=50)
    image = models.ImageField(default="", upload_to=create_filename)
    password_reset_token = models.CharField(default="", max_length=128)
    password_reset_token_expiry = models.IntegerField(default=0)
    company = models.CharField(max_length=100, default="")
    department = models.CharField(max_length=100, default="")
    location = models.CharField(max_length=100, default="")
    lab = models.CharField(max_length=100, default="")
    job_title = models.CharField(max_length=100, default="")

    def __str__(self):
        return f"{self.name} ({self.username})"
    

    @staticmethod
    def from_token(token):
        """Takes a JWT, and if it's signed properly, isn't expired, and points
        to an actual user, returns that user."""

        try:
            token = jwt.decode(token, settings.SECRET_KEY)
            assert token["expires"] > time.time()
            user = User.objects.get(id=token["sub"])
        except: user = None
        return user


    def set_password(self, password):
        """"Sets the user's password, salting and hashing whatever is given
        using Django's built in functions."""

        self.password = make_password(password)
        self.save()
    

    def make_access_jwt(self):
        """Creates and signs an access token indicating the user who signed and
        the time it was signed. It will also indicate that it expires in 15
        minutes."""
        
        now = int(time.time())
        return jwt.encode({
            "sub": self.id, "iat": now, "expires": now + 900
        }, settings.SECRET_KEY, algorithm="HS256").decode()
    

    def make_refresh_jwt(self):
        """Creates and signs an refresh token indicating the user who signed and
        the time it was signed. It will also indicate that it expires in 365
        days."""
        
        now = int(time.time())
        return jwt.encode({
            "sub": self.id, "iat": now, "expires": now + 31536000
        }, settings.SECRET_KEY, algorithm="HS256").decode()
    

    @property
    def admin_groups(self):
        """Groups with admin permissions."""

        return Group.objects.filter(
            usergrouplink__user=self, usergrouplink__permission=3
        )
    

    @property
    def memberships(self):
        """Groups user has access to."""

        return Group.objects.filter(
            usergrouplink__user=self, usergrouplink__permission__gte=2
        )
    

    @property
    def invitations(self):
        """Groups user is invoted to but not a member of."""

        return Group.objects.filter(
            usergrouplink__user=self, usergrouplink__permission=1
        )
    

    @property
    def owned_collections(self):
        """Collections with owner permissions."""

        return Collection.objects.filter(
            collectionuserlink__user=self, collectionuserlink__permission=4,
        )
    

    @property
    def shareable_collections(self):
        """Collections with share permissions."""

        return Collection.objects.filter(
            collectionuserlink__user=self, collectionuserlink__permission__gte=3,
        )
    

    @property
    def editable_collections(self):
        """Collections with edit permissions."""

        return Collection.objects.filter(
            collectionuserlink__user=self, collectionuserlink__permission__gte=2,
        )
    

    @property
    def shareable_samples(self):
        """Samples with share permissions."""

        return Sample.objects.filter(
            sampleuserlink__user=self, sampleuserlink__permission__gte=3,
        )
    

    @property
    def editable_samples(self):
        """Samples with edit permissions."""

        return Sample.objects.filter(
            sampleuserlink__user=self, sampleuserlink__permission__gte=2,
        )
    

    @property
    def owned_executions(self):
        """Executions with owner permissions."""

        return Execution.objects.filter(
            executionuserlink__user=self, executionuserlink__permission=4,
        )
    

    @property
    def shareable_executions(self):
        """Executions with share permissions."""

        return Execution.objects.filter(
            executionuserlink__user=self, executionuserlink__permission__gte=3,
        )
    

    @property
    def editable_executions(self):
        """Executions with edit permissions."""

        return Execution.objects.filter(
            executionuserlink__user=self, executionuserlink__permission__gte=2,
        )



class Group(RandomIDModel):
    """A group that a user belongs to."""

    class Meta:
        db_table = "groups"
    
    name = models.CharField(max_length=50)
    slug = models.SlugField(max_length=50, unique=True, validators=[slug_validator])
    description = models.CharField(max_length=200)
    users = models.ManyToManyField(User, through="core.UserGroupLink", related_name="groups")

    def __str__(self):
        return self.name
    

    @property
    def admins(self):
        """Users with admin permissions."""

        return User.objects.filter(
            usergrouplink__group=self, usergrouplink__permission=3
        )
    

    @property
    def members(self):
        """Users admitted to the group."""

        return User.objects.filter(
            usergrouplink__group=self, usergrouplink__permission__gte=2
        )
    

    @property
    def invitees(self):
        """Users invited to the group."""

        return User.objects.filter(
            usergrouplink__group=self, usergrouplink__permission=1
        )
    

    @property
    def shareable_collections(self):
        """Collections with share permissions."""

        return Collection.objects.filter(
            collectiongrouplink__group=self, collectiongrouplink__permission=3,
        )
    

    @property
    def editable_collections(self):
        """Collections with edit permissions."""

        return Collection.objects.filter(
            collectiongrouplink__group=self, collectiongrouplink__permission__gte=2,
        )



class CollectionQuerySet(models.query.QuerySet):

    def viewable_by(self, user):
        viewable = self.filter(private=False)
        if user:
            viewable |= self.filter(users=user)
            for group in user.groups.all():
                viewable |= self.filter(groups=group)
        return viewable.all().distinct()



class CollectionManager(models.Manager):
    _queryset_class = CollectionQuerySet



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
    users = models.ManyToManyField(User, through="core.CollectionUserLink", related_name="collections")
    groups = models.ManyToManyField(Group, through="core.CollectionGroupLink", related_name="collections")

    objects = CollectionManager()

    def __str__(self):
        return self.name


    def save(self, *args, **kwargs):
        """If the model is being updated, change the last_modified time."""
        
        if self._state.adding is False:
            self.last_modified = int(time.time())
        super(Collection, self).save(*args, **kwargs)
    

    @property
    def owners(self):
        """Users with owner permissions."""

        return User.objects.filter(
            collectionuserlink__collection=self, collectionuserlink__permission=4,
        )
    

    @property
    def sharers(self):
        """Users with share permissions."""

        return User.objects.filter(
            collectionuserlink__collection=self, collectionuserlink__permission__gte=3,
        )
    

    @property
    def editors(self):
        """Users with edit permissions."""

        return User.objects.filter(
            collectionuserlink__collection=self, collectionuserlink__permission__gte=2,
        )
    

    @property
    def group_sharers(self):
        """Groups with share permissions."""

        return Group.objects.filter(
            collectiongrouplink__collection=self, collectiongrouplink__permission=3,
        )
    

    @property
    def group_editors(self):
        """Groups with edit permissions."""

        return Group.objects.filter(
            collectiongrouplink__collection=self, collectiongrouplink__permission__gte=2,
        )
    


class Paper(RandomIDModel):
    """A paper that used data from one or more iMaps collections."""

    class Meta:
        db_table = "papers"
        ordering = ["year"]

    title = models.CharField(max_length=250)
    url = models.URLField(max_length=200, blank=True, null=True)
    year = models.IntegerField()
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE, related_name="papers")



class SampleQuerySet(models.query.QuerySet):

    def viewable_by(self, user):
        viewable = self.filter(private=False)
        if user:
            viewable |= self.filter(users=user)
            viewable |= self.filter(collection__users=user)
            for group in user.groups.all():
                viewable |= self.filter(collection__groups=group)
        return viewable.all().distinct()



class SampleManager(models.Manager):
    _queryset_class = SampleQuerySet



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
    qc_pass = models.NullBooleanField()
    qc_message = models.CharField(max_length=100)
    pi_name = models.CharField(max_length=100)
    annotator_name = models.CharField(max_length=100)
    collection = models.ForeignKey(Collection, null=True, on_delete=models.CASCADE, related_name="samples")
    users = models.ManyToManyField(User, through="core.SampleUserLink", related_name="samples")

    objects = SampleManager()

    def __str__(self):
        return self.name


    def save(self, *args, **kwargs):
        """If the model is being updated, change the last_modified time."""
        
        if self._state.adding is False:
            self.last_modified = int(time.time())
        super(Sample, self).save(*args, **kwargs)
    

    @property
    def sharers(self):
        """Users with share permissions."""

        return User.objects.filter(
            sampleuserlink__sample=self, sampleuserlink__permission=3,
        )
    

    @property
    def editors(self):
        """Users with edit permissions."""

        return User.objects.filter(
            sampleuserlink__sample=self, sampleuserlink__permission__gte=2,
        )



class Command(RandomIDModel):

    class Meta:
        db_table = "commands"
    
    name = models.CharField(max_length=100)
    description = models.TextField()
    nextflow = models.CharField(blank=True, null=True, max_length=200)
    category = models.CharField(max_length=200)
    output_type = models.CharField(max_length=200)
    can_create_sample = models.BooleanField(default=False)

    def __str__(self):
        return self.name
    

    @property
    def output_schema(self):
        with open(os.path.join(settings.NF_ROOT, self.nextflow, "schema.json")) as f:
            return json.load(f)["outputs"]


class ExecutionQuerySet(models.query.QuerySet):

    def viewable_by(self, user):
        viewable = self.filter(private=False)
        if user:
            viewable |= self.filter(users=user)
            viewable |= self.filter(sample__users=user)
            viewable |= self.filter(collection__users=user)
            viewable |= self.filter(sample__collection__users=user)
            for group in user.groups.all():
                viewable |= self.filter(collection__groups=group)
                viewable |= self.filter(sample__collection__groups=group)
        return viewable.all().distinct()


class ExecutionManager(models.Manager):
    _queryset_class = ExecutionQuerySet


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

    input = models.TextField(default="{}")
    output = models.TextField(default="{}")

    command = models.ForeignKey(Command, null=True, on_delete=models.SET_NULL, related_name="executions")
    demultiplex_execution = models.ForeignKey("core.Execution", null=True, blank=True, on_delete=models.SET_NULL, related_name="demultiplexed")
    downstream = models.ManyToManyField("core.Execution", related_name="upstream")
    parent = models.ForeignKey("core.Execution", null=True, blank=True, on_delete=models.SET_NULL, related_name="children")

    private = models.BooleanField(default=True)

    sample = models.ForeignKey(Sample, blank=True, null=True, on_delete=models.SET_NULL, related_name="executions")
    collection = models.ForeignKey(Collection, blank=True, null=True, on_delete=models.SET_NULL, related_name="executions")
    initiator = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL, related_name="initiated_executions")
    users = models.ManyToManyField(User, through="core.ExecutionUserLink", related_name="executions")

    objects = ExecutionManager()


    def __str__(self):
        return self.name
    

    def save(self, *args, **kwargs):
        """If the model is being updated, change the last_modified time."""
        
        if self._state.adding is False:
            self.last_modified = int(time.time())
        super(Execution, self).save(*args, **kwargs)
    

    @property
    def owners(self):
        """Users with owner permissions."""

        return User.objects.filter(
            executionuserlink__execution=self, executionuserlink__permission=4,
        )
    

    @property
    def sharers(self):
        """Users with share permissions."""

        return User.objects.filter(
            executionuserlink__execution=self, executionuserlink__permission__gte=3,
        )
    

    @property
    def editors(self):
        """Users with edit permissions."""

        return User.objects.filter(
            executionuserlink__execution=self, executionuserlink__permission__gte=2,
        )
    

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
        inputs the user supplied when the execution object was created."""

        params = []
        for input in json.loads(self.input):
            if input["type"] == "file":
                params.append(f"--{input['name']} {input['value']['file']}")
        params = " ".join(params)
        config = os.path.join(settings.NF_ROOT, self.command.nextflow, "nextflow.config")
        return run(
            f"nextflow -C {config} run run.nf {params}".split(),
            stdout=PIPE, stderr=PIPE, universal_newlines=True, cwd=os.path.join(
                settings.DATA_ROOT, str(self.id)
            )
        )
    

    def fetch_terminal_from_workdir(self):
        """If a Nextflow process fails, it doesn't collect any produced files,
        so you have to manually go and get them from the work directory. This
        function extracts the output.txt file, which contains the error message
        generated by whatever made the process fail, and moves it to the main
        execution directory."""

        directory = os.path.join(settings.DATA_ROOT, str(self.id), "work")
        dirs = os.listdir(directory)
        if dirs: directory = os.path.join(directory, dirs[0])
        dirs = os.listdir(directory)
        if dirs: directory = os.path.join(directory, dirs[0])
        if "output.txt" in os.listdir(directory):
            shutil.copy(
                os.path.join(directory, "output.txt"),
                os.path.join(settings.DATA_ROOT, str(self.id), "output.txt")
            )
    

    @property
    def terminal(self):
        """Gets the output of the execution once finished as a string."""

        directory = os.path.join(settings.DATA_ROOT, str(self.id))
        try:
            with open(os.path.join(directory, "output.txt")) as f:
                return f.read()
        except FileNotFoundError:
            try:
                with open(os.path.join(directory, "stdout.txt")) as f:
                    return f.read()
            except FileNotFoundError: return ""

    

    def collect_outputs_from_directory(self):
        """Populates the execution object's `output` field after it has run, by
        looking at any files produced and any values printed during the run."""

        outputs = []
        schema = self.command.output_schema
        terminal_output = self.terminal.splitlines()
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
                for line in terminal_output:
                    if line.startswith(output["match"]):
                        outputs.append({
                            "name": output["name"], "type": "basic",
                            "value": line[len(output["match"]):].strip()
                        })
                        terminal_output.remove(line)
                        break
        self.output = json.dumps(outputs)
        self.save()
        with open(os.path.join(directory, "output.txt"), "w") as f:
            f.write("\n".join(terminal_output))



class UserGroupLink(models.Model):
    """Describes the nature of the relationship between a user and group."""

    class Meta:
        db_table = "user_group_links"
    
    PERMISSIONS = [[1, "invited"], [2, "member"], [3, "admin"]]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    permission = models.IntegerField(choices=PERMISSIONS, default=1)



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



class ExecutionUserLink(models.Model):
    """Describes the nature of the relationship between a user and execution."""

    class Meta:
        db_table = "execution_user_links"
    
    PERMISSIONS = [[1, "access"], [2, "edit"], [3, "share"], [4, "own"]]

    execution = models.ForeignKey(Execution, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    permission = models.IntegerField(choices=PERMISSIONS, default=1)