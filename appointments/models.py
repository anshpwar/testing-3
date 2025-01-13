from django.db import models


class Appointment(models.Model):
    STATUSES = [("booked", "Booked"), ("completed", "Completed"), ("cancelled", "Cancelled"), ("no_show", "No show")]

    patient = models.ForeignKey("patients.Patient", on_delete=models.PROTECT, related_name="appointments")
    clinician = models.ForeignKey("staff.Clinician", on_delete=models.PROTECT, related_name="appointments")
    starts_at = models.DateTimeField()
    duration_min = models.PositiveSmallIntegerField(default=20)
    status = models.CharField(max_length=10, choices=STATUSES, default="booked")
    reason = models.CharField(max_length=120, blank=True, default="")
    room = models.CharField(max_length=8, blank=True, default="")  # v2
    cancel_reason = models.CharField(max_length=120, blank=True, default="")  # v2

    class Meta:
        ordering = ["starts_at"]

    def __str__(self):
        return f"{self.patient.mrn} with {self.clinician.employee_no} at {self.starts_at:%Y-%m-%d %H:%M}"
