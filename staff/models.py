from django.db import models


class Department(models.Model):
    code = models.CharField(max_length=8, unique=True)
    name = models.CharField(max_length=80)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return self.code


class Clinician(models.Model):
    ROLES = [("physician", "Physician"), ("nurse", "Nurse"), ("pharmacist", "Pharmacist"),
             ("technician", "Lab technician"), ("admin", "Administrator")]

    employee_no = models.CharField(max_length=12, unique=True)
    family_name = models.CharField(max_length=60)
    given_name = models.CharField(max_length=60)
    role = models.CharField(max_length=12, choices=ROLES)
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name="clinicians")
    license_no = models.CharField(max_length=20, blank=True, default="")
    active = models.BooleanField(default=True)
    supervisor = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="reports")  # v2
    on_call = models.BooleanField(default=False)  # v2

    class Meta:
        ordering = ["family_name", "given_name"]

    def __str__(self):
        return f"{self.family_name}, {self.given_name} ({self.role})"

    @property
    def can_prescribe(self):
        return self.active and self.role == "physician"
