"""Patient registration and demographic lookups."""
from clinkit import clinical, identifiers

from .models import Allergy, EmergencyContact, Patient


def next_mrn(prefix="MRN"):
    seq = Patient.objects.count() + 1
    mrn = identifiers.make_mrn(seq, prefix)
    while Patient.objects.filter(mrn=mrn).exists():
        seq += 1
        mrn = identifiers.make_mrn(seq, prefix)
    return mrn


def register(family_name, given_name, birth_date, sex="U", phone="", weight_kg=None, height_cm=None, **extra):
    if phone:
        phone = identifiers.normalise_phone(phone)
    return Patient.objects.create(mrn=next_mrn(), family_name=family_name.strip(), given_name=given_name.strip(),
                                  birth_date=birth_date, sex=sex, phone=phone, weight_kg=weight_kg,
                                  height_cm=height_cm, **extra)


def record_allergy(patient, substance, severity, recorded_on):
    allergy, _ = Allergy.objects.update_or_create(
        patient=patient, substance=substance.strip().lower(),
        defaults={"severity": severity, "recorded_on": recorded_on})
    return allergy


def add_contact(patient, name, relationship, phone, primary=False):
    if primary:
        patient.contacts.update(is_primary=False)
    return EmergencyContact.objects.create(patient=patient, name=name, relationship=relationship,
                                           phone=identifiers.normalise_phone(phone), is_primary=primary)


def primary_contact(patient):
    return patient.contacts.filter(is_primary=True).first() or patient.contacts.first()


def profile(patient, on):
    """Demographic summary used by the patient page and the ward census."""
    data = {
        "mrn": patient.mrn,
        "name": patient.display_name,
        "age": clinical.age_years(patient.birth_date, on),
        "allergies": sorted(a.substance for a in patient.allergies.all()),
        "blood_type": patient.blood_type,
    }
    if patient.weight_kg and patient.height_cm:
        data["bmi"] = str(clinical.bmi(patient.weight_kg, patient.height_cm))
    return data
