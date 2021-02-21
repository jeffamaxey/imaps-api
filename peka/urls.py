from django.urls import path
from .views import *

urlpatterns = [
    path("entities/", entities),
    path("rbp", rbp),
    path("motif", motif),
    path("", data),
]