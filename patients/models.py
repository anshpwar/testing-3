from django.db import models


class Patient(models.Model):
    SEXES = [("M", "Male"), ("F", "Female"), ("O", "Other"), ("U", "Unknown")]

    mrn = models.CharField(max_length=14, unique=True)
    family_name = models.CharField(max_length=60)
    given_name = models.CharField(max_length=60)
    birth_date = models.DateField()
    sex = models.CharField(max_length=1, choices=SEXES, default="U")
    phone = models.CharField(max_length=20, blank=True, default="")
    weight_kg = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    height_cm = models.PositiveSmallIntegerField(null=True, blank=True)
    active = models.BooleanField(default=True)
    blood_type = models.CharField(max_length=3, blank=True, default="")  # v2
    insurer = models.ForeignKey("billing.Insurer", null=True, blank=True, on_delete=models.SET_NULL, related_name="members")  # v2
    member_no = models.CharField(max_length=20, blank=True, default="")  # v2

    class Meta:
        ordering = ["family_name", "given_name", "mrn"]

    def __str__(self):
        return f"{self.family_name}, {self.given_name} [{self.mrn}]"

    @property
    def display_name(self):
        return f"{self.given_name} {self.family_name}"


class Allergy(models.Model):
    SEVERITIES = [("mild", "Mild"), ("moderate", "Moderate"), ("severe", "Severe")]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="allergies")
    substance = models.CharField(max_length=80)
    severity = models.CharField(max_length=10, choices=SEVERITIES, default="moderate")
    recorded_on = models.DateField()

    class Meta:
        unique_together = [("patient", "substance")]
        verbose_name_plural = "allergies"

    def __str__(self):
        return f"{self.substance} ({self.severity})"


# v2-begin
class EmergencyContact(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="contacts")
    name = models.CharField(max_length=80)
    relationship = models.CharField(max_length=30)
    phone = models.CharField(max_length=20)
    is_primary = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} ({self.relationship})"
# v2-end
