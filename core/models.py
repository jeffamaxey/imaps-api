from django.db import models
from django.contrib.auth.hashers import make_password

class User(models.Model):
    """The user model."""

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