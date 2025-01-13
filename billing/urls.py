from django.urls import path

from . import views

urlpatterns = [
    path("invoices/<str:number>/", views.statement, name="invoice-statement"),
    path("invoices/<str:number>/pay/", views.pay, name="invoice-pay"),
]
