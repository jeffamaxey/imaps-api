import time
import jwt
import json
import base64
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



class Group(RandomIDModel):
    """A group that a user belongs to."""

    class Meta:
        db_table = "groups"
    
    name = models.CharField(max_length=50)
    slug = models.SlugField(max_length=50, unique=True, validators=[slug_validator])
    description = models.CharField(max_length=200)
    users = models.ManyToManyField(User, related_name="groups")
    admins = models.ManyToManyField(User, related_name="admin_groups")

    def __str__(self):
        return self.name



class GroupInvitation(RandomIDModel):
    """An invitation to a group."""

    class Meta:
        db_table = "group_invitations"
        ordering = ["created"]

    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="group_invitations")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="group_invitations")
    created = models.IntegerField(default=time.time)

    def __str__(self):
        return f"{self.group.name} invitation to {self.user.name}"
    


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
        
        if self.id:
            self.last_modified = int(time.time())
        super(Collection, self).save(*args, **kwargs)
    


class CollectionUserLink(models.Model):
    """Describes the nature of the relationship between a user and
    collection."""

    class Meta:
        db_table = "collection_user_links"

    collection = models.ForeignKey(Collection, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    can_edit = models.BooleanField(default=False)
    can_share = models.BooleanField(default=False)
    is_owner = models.BooleanField(default=False)



class CollectionGroupLink(models.Model):
    """Describes the nature of the relationship between a group and
    collection."""

    class Meta:
        db_table = "collection_group_links"

    collection = models.ForeignKey(Collection, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    can_edit = models.BooleanField(default=False)
    can_share = models.BooleanField(default=False)



class Paper(RandomIDModel):
    """A paper that used data from one or more iMaps collections."""

    class Meta:
        db_table = "papers"
        ordering = ["year"]

    title = models.CharField(max_length=250)
    url = models.URLField(max_length=200, blank=True, null=True)
    year = models.IntegerField()
    journal = models.CharField(max_length=100)
    doi = models.CharField(max_length=100)
    collections = models.ManyToManyField(Collection, related_name="papers")



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
        
        if self.id:
            self.last_modified = int(time.time())
        super(Sample, self).save(*args, **kwargs)



class SampleUserLink(models.Model):
    """Describes the nature of the relationship between a user and
    sample."""

    class Meta:
        db_table = "sample_user_links"

    sample = models.ForeignKey(Sample, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    can_edit = models.BooleanField(default=False)
    can_share = models.BooleanField(default=False)



class Command(RandomIDModel):

    class Meta:
        db_table = "commands"
    
    name = models.CharField(max_length=100)
    description = models.TextField()
    input_schema = models.TextField(default="[]")
    output_schema = models.TextField(default="[]")

    def __str__(self):
        return self.name


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
    scheduled = models.IntegerField(blank=True, null=True)
    started = models.IntegerField(blank=True, null=True)
    finished = models.IntegerField(blank=True, null=True)
    status = models.CharField(max_length=50, blank=True, null=True)
    private = models.BooleanField(default=True)
    warning = models.TextField(blank=True, null=True)
    error = models.TextField(blank=True, null=True)
    input = models.TextField(default="{}")
    output = models.TextField(default="{}")
    user = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL, related_name="created_executions")
    sample = models.ForeignKey(Sample, blank=True, null=True, on_delete=models.SET_NULL, related_name="executions")
    collection = models.ForeignKey(Collection, blank=True, null=True, on_delete=models.SET_NULL, related_name="executions")
    command = models.ForeignKey(Command, null=True, on_delete=models.SET_NULL, related_name="executions")
    users = models.ManyToManyField(User, through="core.ExecutionUserLink", related_name="executions")

    objects = ExecutionManager()


    def __str__(self):
        return self.name
    

    @property
    def parent(self):
        """Identifies the execution that spawned this one as a subcommand, if
        any."""

        possibles = Execution.objects.filter(output__contains=str(self.id))
        for possible in possibles:
            output = json.loads(possible.output)
            if "steps" in output and int(self.id) in output["steps"]:
                return possible
    

    @property
    def upstream(self):
        """Identifies the executions whose products this execution consumes."""

        input_schema = json.loads(self.command.input_schema)
        inputs = json.loads(self.input)
        ids = []
        for inp in input_schema:
            if inp["name"] in inputs and "type" in inp:
                if inp["type"].startswith("data:"):
                    ids.append(inputs[inp["name"]])
                if inp["type"].startswith("list:data:"):
                    ids += inputs[inp["name"]]
        return Execution.objects.filter(id__in=ids)
    

    @property
    def downstream(self):
        """Identifies the executions which consume this execution's products."""

        possibles = Execution.objects.filter(input__contains=f"{self.id}")
        possibles = possibles.select_related("command")
        confirmed_ids = set()
        for possible in possibles:
            input_schema = json.loads(possible.command.input_schema)
            inputs = json.loads(possible.input)
            for inp in input_schema:
                if inp["name"] in inputs and "type" in inp:
                    if inp["type"][:4] == "data" and inputs[inp["name"]] == self.id:
                        confirmed_ids.add(possible.id)
                    if inp["type"][:9] == "list:data" and self.id in inputs[inp["name"]]:
                        confirmed_ids.add(possible.id)
        return Execution.objects.filter(id__in=confirmed_ids)
    

    @property
    def components(self):
        """Identifies the executions spawned by this execution as
        subcommandes."""

        outputs = json.loads(self.output)
        steps = outputs.get("steps", [])
        return Execution.objects.filter(id__in=steps)




class ExecutionUserLink(models.Model):
    """Describes the nature of the relationship between a user and
    execution."""

    class Meta:
        db_table = "execution_user_links"

    execution = models.ForeignKey(Execution, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    can_edit = models.BooleanField(default=False)
    can_share = models.BooleanField(default=False)
    is_owner = models.BooleanField(default=False)