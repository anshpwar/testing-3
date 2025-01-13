from django.contrib import admin

from .models import LabOrder, LabResult, LabTest

admin.site.register(LabTest)
admin.site.register(LabResult)


@admin.register(LabOrder)
class LabOrderAdmin(admin.ModelAdmin):
    list_display = ("placer_no", "patient", "test", "status")
