from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("patients/", include("patients.urls")),
    path("appointments/", include("appointments.urls")),
    path("prescriptions/", include("prescriptions.urls")),
    path("wards/", include("wards.urls")),
    path("labs/", include("labs.urls")),
    path("billing/", include("billing.urls")),
    path("entries/", include("encounters.urls")),
]
