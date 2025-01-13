from django.contrib import admin

from .models import Clinician, Department


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("code", "name")


@admin.register(Clinician)
class ClinicianAdmin(admin.ModelAdmin):
    list_display = ("employee_no", "family_name", "role", "department", "active")
    list_filter = ("role", "department", "active")
