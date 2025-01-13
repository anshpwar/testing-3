from django.urls import path

from . import views

urlpatterns = [
    path("<str:code>/census/", views.census, name="ward-census"),
    path("<str:code>/admit/", views.admit, name="ward-admit"),
]
