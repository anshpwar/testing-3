from django.urls import path

from . import views

urlpatterns = [
    path("hl7/", views.receive_hl7, name="lab-hl7"),
    path("orders/<str:placer_no>/", views.order_detail, name="lab-order"),
]
