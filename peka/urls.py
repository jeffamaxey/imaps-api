from django.urls import path
from .views import data, rbp

urlpatterns = [
    path("rbp", rbp),
    path("", data),
]