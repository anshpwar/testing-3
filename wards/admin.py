from django.contrib import admin

from .models import Admission, Bed, Ward


class BedInline(admin.TabularInline):
    model = Bed
    extra = 0


@admin.register(Ward)
class WardAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "department", "level")
    inlines = [BedInline]


admin.site.register(Admission)
