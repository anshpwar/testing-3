from django.db import models


class Insurer(models.Model):
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=80)
    plan_tier = models.PositiveSmallIntegerField(default=1)

    def __str__(self):
        return self.code


class Invoice(models.Model):
    STATUSES = [("draft", "Draft"), ("issued", "Issued"), ("paid", "Paid"), ("void", "Void")]

    patient = models.ForeignKey("patients.Patient", on_delete=models.PROTECT, related_name="invoices")
    number = models.CharField(max_length=20, unique=True)
    issued_on = models.DateField()
    status = models.CharField(max_length=8, choices=STATUSES, default="draft")
    due_days = models.PositiveSmallIntegerField(default=30)  # v2

    class Meta:
        ordering = ["number"]

    def __str__(self):
        return self.number


class InvoiceLine(models.Model):
    KINDS = [("consult", "Consultation"), ("bed", "Bed day"), ("lab", "Laboratory"), ("pharmacy", "Pharmacy"), ("other", "Other")]

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="lines")
    kind = models.CharField(max_length=10, choices=KINDS, default="other")
    description = models.CharField(max_length=120)
    qty = models.PositiveIntegerField(default=1)
    unit_cents = models.BigIntegerField()
    appointment = models.ForeignKey("appointments.Appointment", null=True, blank=True, on_delete=models.SET_NULL, related_name="invoice_lines")  # v2
    admission = models.ForeignKey("wards.Admission", null=True, blank=True, on_delete=models.SET_NULL, related_name="invoice_lines")  # v2
    lab_order = models.ForeignKey("labs.LabOrder", null=True, blank=True, on_delete=models.SET_NULL, related_name="invoice_lines")  # v2

    @property
    def total_cents(self):
        return self.qty * self.unit_cents


class Payment(models.Model):
    METHODS = [("card", "Card"), ("cash", "Cash"), ("transfer", "Bank transfer"), ("insurer", "Insurer remittance")]

    invoice = models.ForeignKey(Invoice, on_delete=models.PROTECT, related_name="payments")
    amount_cents = models.BigIntegerField()
    method = models.CharField(max_length=10, choices=METHODS, default="card")
    received_on = models.DateField()
    reference = models.CharField(max_length=40, blank=True, default="")  # v2
