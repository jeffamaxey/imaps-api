import time
import jwt
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
        ordering = ["creation_time"]

    username = models.SlugField(max_length=30, unique=True, validators=[slug_validator])
    email = models.EmailField(max_length=200, unique=True)
    password = models.CharField(max_length=128)
    last_login = models.IntegerField(null=True, default=None)
    creation_time = models.IntegerField(default=0)
    name = models.CharField(max_length=50)
    image = models.ImageField(default="", upload_to=create_filename)
    password_reset_token = models.CharField(default="", max_length=128)
    password_reset_token_expiry = models.IntegerField(default=0)

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
    

    def save(self, *args, **kwargs):
        """If the model is being saved for the first time, set the creation
        time."""
        
        if not self.id:
            self.creation_time = int(time.time())
        super(User, self).save(*args, **kwargs)
    

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
        ordering = ["creation_time"]

    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="group_invitations")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="group_invitations")
    creation_time = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.group.name} invitation to {self.user.name}"
    

    def save(self, *args, **kwargs):
        """If the model is being saved for the first time, set the creation
        time."""
        
        if not self.id:
            self.creation_time = int(time.time())
        super(GroupInvitation, self).save(*args, **kwargs)



class Collection(RandomIDModel):
    """A collection of samples that belong together in some sense, either as
    part of a single paper or to answer a single research question.
    
    It is either private or not, which determies whether the public can view it.
    
    It has a single owner, which is a user with full permissions. It can be
    associated with multiple other users, who will have varying permissions, as
    well as multiple groups, with varying permissions."""

    class Meta:
        db_table = "collections"
        ordering = ["-creation_time"]

    name = models.CharField(max_length=50)
    creation_time = models.IntegerField(default=time.time)
    last_modified = models.IntegerField(default=time.time)
    description = models.TextField(default="", blank=True)
    private = models.BooleanField(default=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="owned_collections")
    users = models.ManyToManyField(User, through="core.CollectionUserLink", related_name="collections")
    groups = models.ManyToManyField(Group, through="core.CollectionGroupLink", related_name="collections")


    def save(self, *args, **kwargs):
        """If the model is being updated, change the last_modified time."""
        
        if self.id:
            self.last_modified = int(time.time())
        super(Collection, self).save(*args, **kwargs)
    

    def editable_by(self, user):
        """Determines if a user should be able to edit the collection."""

        if user is None: return False
        if self.owner == user: return True
        if self.users.filter(id=user.id):
            if self.collectionuserlink_set.get(user=user).can_edit: return True
        user_groups = list(user.groups.all())
        collection_groups = list(self.groups.all())
        for user_group in user_groups:
            for collection_group in collection_groups:
                if user_group.id == collection_group.id:
                    return self.collectiongrouplink_set.get(
                        group=collection_group
                    ).can_edit
        return False
    

    def executable_by(self, user):
        """Determines if a user should be able to edit the collection."""

        if user is None: return False
        if self.owner == user: return True
        if self.users.filter(id=user.id):
            if self.collectionuserlink_set.get(user=user).can_execute: return True
        user_groups = list(user.groups.all())
        collection_groups = list(self.groups.all())
        for user_group in user_groups:
            for collection_group in collection_groups:
                if user_group == collection_group:
                    return self.collectiongrouplink_set.get(
                        group=collection_group
                    ).can_execute
        return False



class CollectionUserLink(models.Model):
    """Describes the nature of the relationship between a user and
    collection."""

    class Meta:
        db_table = "collection_user_links"

    collection = models.ForeignKey(Collection, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    can_edit = models.BooleanField(default=True)
    can_execute = models.BooleanField(default=False)



class CollectionGroupLink(models.Model):
    """Describes the nature of the relationship between a group and
    collection."""

    class Meta:
        db_table = "collection_group_links"

    collection = models.ForeignKey(Collection, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    can_edit = models.BooleanField(default=True)
    can_execute = models.BooleanField(default=False)



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



class Sample(RandomIDModel):
    """A single CLIP experiment."""

    class Meta:
        db_table = "samples"
        ordering = ["-creation_time"]
    
    name = models.CharField(max_length=50)
    creation_time = models.IntegerField(default=time.time)
    last_modified = models.IntegerField(default=time.time)
    description = models.TextField(default="", blank=True)
    source = models.CharField(max_length=100)
    organism = models.CharField(max_length=100)
    qc_pass = models.NullBooleanField()
    qc_message = models.CharField(max_length=100)
    pi_name = models.CharField(max_length=100)
    annotator_name = models.CharField(max_length=100)
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE, related_name="samples")

    def save(self, *args, **kwargs):
        """If the model is being updated, change the last_modified time."""
        
        if self.id:
            self.last_modified = int(time.time())
        super(Sample, self).save(*args, **kwargs)