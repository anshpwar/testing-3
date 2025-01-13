"""Shared fixtures for the domain tests. Everything is deterministic: fixed dates, fixed sequence numbers."""
import datetime as dt

from billing.models import Insurer
from clinkit import identifiers
from labs.models import LabTest
from patients.models import Patient
from prescriptions.models import Medication
from staff.models import Clinician, Department
from wards.models import Bed, Ward

UTC = dt.timezone.utc
DAY = dt.datetime(2025, 3, 3, 9, 0, tzinfo=UTC)


def department(code="MED", name="Internal medicine"):
    return Department.objects.get_or_create(code=code, defaults={"name": name})[0]


def clinician(employee_no="E100", role="physician", family="Okafor", given="Adaeze", dept=None, **extra):
    return Clinician.objects.create(employee_no=employee_no, family_name=family, given_name=given, role=role,
                                    department=dept or department(), **extra)


def patient(seq=1, weight="70.0", birth=dt.date(1980, 6, 15), insurer=None, **extra):
    return Patient.objects.create(mrn=identifiers.make_mrn(seq), family_name=f"Testson{seq}", given_name="Pat",
                                  birth_date=birth, sex="F", weight_kg=weight, height_cm=170, insurer=insurer, **extra)


def insurer(tier=2, code="NORTHWIND"):
    return Insurer.objects.create(code=code, name=f"{code.title()} Health", plan_tier=tier)


def medication(code="AMOX500", name="Amoxicillin", strength=500, schedule=0, sedating=False):
    return Medication.objects.create(code=code, name=name, strength_mg=strength, schedule=schedule, sedating=sedating)


def lab_test(code="K", name="Potassium", unit="mmol/L", low="3.5", high="5.1"):
    return LabTest.objects.create(code=code, name=name, unit=unit, ref_low=low, ref_high=high)


def ward(code="W1", level=1, dept=None, beds=("A1", "A2", "A3")):
    w = Ward.objects.create(code=code, name=f"Ward {code}", department=dept or department(), level=level)
    for label in beds:
        Bed.objects.create(ward=w, label=label)
    return w
