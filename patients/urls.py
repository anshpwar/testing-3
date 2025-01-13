from django.urls import path

from . import views

urlpatterns = [
    path("", views.register, name="patient-register"),
    path("<str:mrn>/", views.detail, name="patient-detail"),
    path("<str:mrn>/page/", views.page, name="patient-page"),
]
