from django.db import models


class Ward(models.Model):
    code = models.CharField(max_length=8, unique=True)
    name = models.CharField(max_length=80)
    department = models.ForeignKey("staff.Department", on_delete=models.PROTECT, related_name="wards")
    level = models.PositiveSmallIntegerField(default=1, help_text="Acuity level, 1 (general) to 4 (intensive)")

    def __str__(self):
        return self.code


class Bed(models.Model):
    STATUSES = [("free", "Free"), ("occupied", "Occupied"), ("cleaning", "Cleaning"), ("closed", "Out of service")]

    ward = models.ForeignKey(Ward, on_delete=models.CASCADE, related_name="beds")
    label = models.CharField(max_length=8)
    status = models.CharField(max_length=10, choices=STATUSES, default="free")
    isolation = models.BooleanField(default=False)  # v2

    class Meta:
        unique_together = [("ward", "label")]
        ordering = ["ward", "label"]

    def __str__(self):
        return f"{self.ward.code}/{self.label}"


class Admission(models.Model):
    patient = models.ForeignKey("patients.Patient", on_delete=models.PROTECT, related_name="admissions")
    bed = models.ForeignKey(Bed, on_delete=models.PROTECT, related_name="admissions")
    attending = models.ForeignKey("staff.Clinician", on_delete=models.PROTECT, related_name="admissions")
    admitted_at = models.DateTimeField()
    discharged_at = models.DateTimeField(null=True, blank=True)
    discharge_note = models.CharField(max_length=200, blank=True, default="")  # v2

    class Meta:
        ordering = ["-admitted_at"]

    @property
    def is_open(self):
        return self.discharged_at is None
