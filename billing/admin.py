from django.contrib import admin

from .models import Insurer, Invoice, InvoiceLine, Payment


class LineInline(admin.TabularInline):
    model = InvoiceLine
    extra = 0


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("number", "patient", "status", "issued_on")
    inlines = [LineInline]


admin.site.register(Insurer)
admin.site.register(Payment)
