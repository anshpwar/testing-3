from django.db import models


class LabTest(models.Model):
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=80)
    unit = models.CharField(max_length=16)
    ref_low = models.DecimalField(max_digits=10, decimal_places=3)
    ref_high = models.DecimalField(max_digits=10, decimal_places=3)

    def __str__(self):
        return self.code


class LabOrder(models.Model):
    STATUSES = [("ordered", "Ordered"), ("collected", "Collected"), ("resulted", "Resulted"), ("cancelled", "Cancelled")]

    patient = models.ForeignKey("patients.Patient", on_delete=models.PROTECT, related_name="lab_orders")
    ordering = models.ForeignKey("staff.Clinician", on_delete=models.PROTECT, related_name="lab_orders")
    test = models.ForeignKey(LabTest, on_delete=models.PROTECT, related_name="orders")
    priority = models.PositiveSmallIntegerField(default=3)
    status = models.CharField(max_length=10, choices=STATUSES, default="ordered")
    placer_no = models.CharField(max_length=20, unique=True)
    ordered_at = models.DateTimeField()

    class Meta:
        ordering = ["ordered_at", "id"]


class LabResult(models.Model):
    FLAGS = [("N", "Normal"), ("L", "Low"), ("H", "High"), ("LL", "Critical low"), ("HH", "Critical high")]

    order = models.OneToOneField(LabOrder, on_delete=models.CASCADE, related_name="result")
    value = models.DecimalField(max_digits=12, decimal_places=3)
    flag = models.CharField(max_length=2, choices=FLAGS, default="N")
    reported_at = models.DateTimeField()
    source_message = models.CharField(max_length=40, blank=True, default="")  # v2
