from django.forms import ModelForm, Form, CharField
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.hashers import check_password
from django.conf import settings
from django.core.exceptions import ValidationError
from core.models import *

class SignupForm(ModelForm):
    """Creates a user object."""

    class Meta:
        model = User
        fields = ["email", "name", "username", "password"]


    def clean_email(self):
        """Lower cases the email."""

        return self.data["email"].lower()


    def clean_password(self):
        """Runs the password validators specified in settings."""

        validate_password(self.data["password"])
        return self.data["password"]

        
    def save(self):
        """Hash password before saving."""

        user = ModelForm.save(self, commit=False)
        user.set_password(self.cleaned_data.get("password"))
        user.save()



class UpdateUserForm(ModelForm):
    """Edits the basid fields of a user."""

    class Meta:
        model = User
        fields = ["username", "name", "email"]
    

    def clean_email(self):
        """Lower cases the email."""

        return self.data["email"].lower()



class UpdatePasswordForm(ModelForm):
    """Edits the password field of a user, and nothing else. Requires the
    current password."""

    class Meta:
        model = User
        fields = []
    
    current = CharField(required=True)
    new = CharField(required=True)

    def clean_current(self):
        """Checks that the supplied current password is currect."""

        if not check_password(self.data["current"], self.instance.password):
            self.add_error("current", "Current password not correct.")
        return self.data["current"]


    def clean_new(self):
        """Runs the password validators specified in settings."""

        validate_password(self.data["new"])
        return self.data["new"]


    def save(self):
        self.instance.set_password(self.cleaned_data.get("new"))



class UpdateUserImageForm(ModelForm):

    class Meta:
        model = User
        fields = ["image"]

    def save(self, *args, **kwargs):
        """Save the uploaded image."""
        
        image = self.data.get("image")
        if not (self.instance.image and not image):
            self.instance.image = self.data.get("image")
        if self.instance.image and not image:
            self.instance.image = ""
        ModelForm.save(self, *args, **kwargs)



class GroupForm(ModelForm):
    """Creates or edits a group."""

    class Meta:
        model = Group
        exclude = ["id", "admins", "users"]



class CollectionForm(ModelForm):
    """Creates or edits a collection."""

    class Meta:
        model = Collection
        exclude = ["id", "users", "groups", "created", "last_modified"]



class PaperForm(ModelForm):
    """Creates or edits a paper."""

    class Meta:
        model = Paper
        exclude = ["id"]



class SampleForm(ModelForm):
    """Creates or edits a sample."""

    class Meta:
        model = Sample
        exclude = ["id", "created", "last_modified", "qc_message", "qc_pass", "users"]