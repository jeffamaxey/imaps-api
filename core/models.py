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

    username = models.SlugField(max_length=30, unique=True)
    email = models.EmailField(max_length=200, unique=True)
    password = models.CharField(max_length=128)
    last_login = models.IntegerField(null=True, default=None)
    name = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.name} ({self.username})"
    

    def set_password(self, password):
        """"Sets the user's password, salting and hashing whatever is given
        using Django's built in functions."""

        self.password = make_password(password)
        self.save()
    

    def make_jwt(self):
        """Creates and signs a token indicating the user who signed and the time
        it was signed."""
        
        return jwt.encode({
            "sub": self.id, "iat": int(time.time())
        }, settings.SECRET_KEY, algorithm="HS256").decode()



class Group(RandomIDModel):
    """A group that a user belongs to."""

    class Meta:
        db_table = "groups"
    
    name = models.CharField(max_length=50, unique=True)
    users = models.ManyToManyField(User, related_name="groups")
    admins = models.ManyToManyField(User, related_name="admin_groups")

    def __str__(self):
        return self.name