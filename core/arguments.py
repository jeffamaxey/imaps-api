import graphene
from graphql import GraphQLError
from django.forms.fields import *
from django.forms.models import ModelChoiceField

def create_mutation_arguments(ModelForm, edit=False, ignore=None):
    """Creates mutation arguments from a modelform. If the edit parameter is set
    to True, an id argument will be added and any parent model fields will be
    ignored."""
    
    ignore = ignore or []
    ignore.append("user")
    d = {"id": graphene.ID(required=True)} if edit else {}
    lookup = {
        BooleanField: graphene.Boolean, FloatField: graphene.Float,
        ModelChoiceField: graphene.ID, DateTimeField: graphene.Float,
        DecimalField: graphene.Float, IntegerField: graphene.Int,
    }
    for name, field in ModelForm.base_fields.items():
        if name not in ignore and (field.__class__ != ModelChoiceField or not edit):
            d[name] = lookup.get(
                field.__class__, graphene.String
            )(required=field.required)
    return type("Arguments", (), d)