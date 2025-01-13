from django.contrib import admin

from .models import Medication, Prescription

admin.site.register(Medication)


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ("patient", "medication", "dose_mg", "status")
