import time
import jwt
import base64
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
    

    def make_jwt(self, ttl):
        """Creates and signs a token indicating the user who signed and the time
        it was signed. It will also indicate when it expires."""
        
        now = int(time.time())
        return jwt.encode({
            "sub": self.id, "iat": now, "expires": now + ttl
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
    users = models.ManyToManyField(User, through="core.UserGroupLink", related_name="groups")

    def __str__(self):
        return self.name



class UserGroupLink(models.Model):
    """Describes the nature of the relationship between a user and group."""

    class Meta:
        db_table = "user_group_links"
    
    PERMISSIONS = [[1, "invited"], [2, "member"], [3, "admin"]]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    permission = models.IntegerField(choices=PERMISSIONS, default=1)