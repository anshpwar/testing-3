from django.contrib import admin

from .models import Allergy, EmergencyContact, Patient


class AllergyInline(admin.TabularInline):
    model = Allergy
    extra = 0


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ("mrn", "family_name", "given_name", "birth_date", "insurer")
    search_fields = ("mrn", "family_name")
    inlines = [AllergyInline]


admin.site.register(EmergencyContact)
