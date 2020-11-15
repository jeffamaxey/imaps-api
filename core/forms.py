from django.forms import ModelForm, Form, CharField
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate
from django.conf import settings
from django.core.exceptions import ValidationError
from core.models import *

class SignupForm(ModelForm):
    """Creates a user object."""

    class Meta:
        model = User
        fields = ["email", "name", "username", "password"]


    def clean_password(self):
        """Runs the password validators specified in settings."""

        validate_password(self.data["password"])
        return self.data["password"]

        
    def save(self):
        """Hash password before saving."""

        user = ModelForm.save(self, commit=False)
        user.set_password(self.cleaned_data.get("password"))
        user.save()