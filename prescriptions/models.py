from django.db import models


class Medication(models.Model):
    code = models.CharField(max_length=12, unique=True)
    name = models.CharField(max_length=80)
    strength_mg = models.PositiveIntegerField()
    schedule = models.PositiveSmallIntegerField(default=0, help_text="0 uncontrolled, 1-4 controlled-substance schedule")
    sedating = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} {self.strength_mg} mg"


class Prescription(models.Model):
    STATUSES = [("active", "Active"), ("completed", "Completed"), ("stopped", "Stopped")]

    patient = models.ForeignKey("patients.Patient", on_delete=models.PROTECT, related_name="prescriptions")
    prescriber = models.ForeignKey("staff.Clinician", on_delete=models.PROTECT, related_name="prescriptions")
    medication = models.ForeignKey(Medication, on_delete=models.PROTECT, related_name="prescriptions")
    dose_mg = models.PositiveIntegerField()
    per_day = models.PositiveSmallIntegerField(default=1)
    days = models.PositiveSmallIntegerField(default=7)
    status = models.CharField(max_length=10, choices=STATUSES, default="active")
    written_on = models.DateField()
    refills = models.PositiveSmallIntegerField(default=0)  # v2
    instructions = models.CharField(max_length=200, blank=True, default="")  # v2

    class Meta:
        ordering = ["-written_on", "-id"]
