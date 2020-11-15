import time
import jwt
from random import randint
from django_random_id_model import RandomIDModel
from django.db import models
from django.conf import settings
from django.contrib.auth.hashers import make_password

class User(RandomIDModel):
    """The user model."""

    class Meta:
        db_table = "users"
        ordering = ["creation_time"]

    username = models.SlugField(max_length=30, unique=True)
    email = models.EmailField(max_length=200, unique=True)
    password = models.CharField(max_length=128)
    last_login = models.IntegerField(null=True, default=None)
    creation_time = models.IntegerField(default=0)
    name = models.CharField(max_length=50)

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
    
    name = models.CharField(max_length=50, unique=True)
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