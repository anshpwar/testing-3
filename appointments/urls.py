from django.urls import path

from . import views

urlpatterns = [
    path("", views.book, name="appointment-book"),
    path("<int:pk>/", views.detail, name="appointment-detail"),
    path("<int:pk>/cancel/", views.cancel, name="appointment-cancel"),
]
