from django.urls import path

from . import views

urlpatterns = [
    path("", views.prescribe, name="prescription-create"),
    path("patient/<str:mrn>/", views.for_patient, name="prescription-list"),
]
