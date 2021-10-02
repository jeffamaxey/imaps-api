from django.urls import path
from .views import *

urlpatterns = [
    path("entities/", entities),
    path("rbp", rbp),
    path("motif/lines", motif_lines),
    path("motif", motif),
    path("", data),
]